import os
import logging
import httpx
from dotenv import load_dotenv
from backend.services.memory import memory_store
from backend.services.retrieval import retriever

load_dotenv(".env.local")
load_dotenv()

logger = logging.getLogger(__name__)

OPENROUTER_API_BASE = "https://openrouter.ai/api/v1"
PRIMARY_MODEL = "meta-llama/llama-3-8b-instruct"
FALLBACK_MODEL = "mistralai/mistral-7b-instruct"
SECONDARY_FALLBACK = "google/gemma-2-9b-it" # No :free per user request, but gemma 2 9b is good

SYSTEM_PROMPT = """You are the SmartSpend AI financial assistant. Your goal is to help users understand their spending, balances, budgets, predicting risk, and alerting them to trends.
Guidelines:
1. Be concise, friendly, and actionable.
2. DO NOT hallucinate numbers. Use the provided Context and user prompt only.
3. If key context is missing, ask a short clarification.
4. Integrate any provided factual Context/FAQs seamlessly.
5. If the request is unclear, politely ask for clarification.
"""


async def _call_openrouter(model: str, messages: list[dict]) -> str:
    api_key = os.getenv("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        logger.error("OPENROUTER_API_KEY is missing")
        return ""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "X-Title": "FinSet SmartSpend Dashboard",
    }
    payload = {
        "model": model,
        "messages": messages,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            logger.info(f"OpenRouter: Sending request to {model}...")
            response = await client.post(f"{OPENROUTER_API_BASE}/chat/completions", headers=headers, json=payload)
            if not response.is_success:
                logger.error(f"OpenRouter API error: {response.status_code} - {response.text}")
                return ""
            
            data = response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
            logger.info(f"OpenRouter: Success. Received {len(content)} characters.")
            return content.strip()
        except Exception as e:
            logger.error(f"HTTP request to OpenRouter failed: {type(e).__name__}: {e}")
            return ""


async def ask_finance_query(session_id: str, question: str) -> dict:
    retrieved_faqs = retriever.retrieve(question, top_k=2)
    faq_context = "Context:\n" + "\n".join(f"- {doc}" for doc in retrieved_faqs) if retrieved_faqs else ""

    messages = [{"role": "system", "content": f"{SYSTEM_PROMPT}\n{faq_context}"}]

    history = memory_store.get_history(session_id, limit=6)
    for msg in history:
        messages.append({"role": msg["role"], "content": msg["content"]})

    messages.append({"role": "user", "content": question})

    answer = "AI assistant temporarily unavailable"
    try:
        answer = await _call_openrouter(PRIMARY_MODEL, messages)
    except Exception:
        logger.exception("Primary OpenRouter model failed")
        try:
            answer = await _call_openrouter(FALLBACK_MODEL, messages)
        except Exception:
            logger.exception("Fallback OpenRouter model failed")
            try:
                answer = await _call_openrouter(SECONDARY_FALLBACK, messages)
            except Exception:
                logger.exception("Secondary fallback failed")
                answer = "AI assistant temporarily unavailable"

    if not answer:
        answer = "AI assistant temporarily unavailable"

    memory_store.add_message(session_id, "user", question)
    memory_store.add_message(session_id, "assistant", answer)

    suggestions = [
        "What is my biggest expense?",
        "Do I have any budget alerts?",
        "Can I afford a new purchase?"
    ]

    return {
        "answer": answer,
        "suggestions": suggestions
    }
