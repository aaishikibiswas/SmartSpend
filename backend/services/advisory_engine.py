from __future__ import annotations
import asyncio
import json
import logging
import random
from backend.services.llm_client import _call_openrouter, PRIMARY_MODEL

logger = logging.getLogger("smartspend.advisory")

async def generate_financial_advice(metrics: dict, budget_snapshot: dict, prediction: dict, expense_split: dict, behavior_profile: dict | None = None) -> dict:
    """
    REBUILT: Fully dynamic Smart Advice system using OpenRouter.
    Identical config to chatbot. No hardcoded static advice.
    """
    
    # 1. Summarize Financial Data
    income = float(metrics.get("totalIncome", 0))
    expenses = float(metrics.get("totalExpense", 0))
    savings = float(metrics.get("netSavings", 0))
    savings_rate = float(metrics.get("savingsRatio", 0))
    
    categories = budget_snapshot.get("categories", [])
    top_cat_item = max(categories, key=lambda x: x.get("spent_amount", 0)) if categories else {"name": "None", "spent_amount": 0}
    top_category = top_cat_item.get("name", "General")
    
    recurring_total = float(metrics.get("subscriptionLoad", 0)) + float(metrics.get("monthlyEmiLoad", 0))

    # 2. Strict LLM Prompt
    prompt = f"""Act as a senior financial advisor inside a premium fintech dashboard.
    
    Context:
    - Income: ₹{income}
    - Expenses: ₹{expenses}
    - Savings: ₹{savings} (Rate: {savings_rate}%)
    - Top Spending: {top_category} (₹{top_cat_item.get('spent_amount')})
    - Recurring commitments: ₹{recurring_total}

    Generate 6-8 distinct, punchy financial advice items.
    
    Each item MUST include:
    - icon: One of ["shield", "trending-up", "landmark", "wallet", "zap", "activity", "target"]
    - label: Short category (e.g., "SAVINGS", "SPENDING", "ZAP", "WEALTH")
    - title: Catchy headline (max 30 chars)
    - body: Actionable insight (max 120 chars)
    - href: A valid dashboard route: ["/budget", "/transactions", "/wallet", "/alerts", "/goals", "/"]
    - action: Call to action text (e.g., "Review Budget", "View History", "Set Goals")

    Rules:
    - Mix personalized advice based on data with general high-value financial wisdom.
    - Vary the 'href' across different routes to make the dashboard interactive.
    - RETURN ONLY A VALID JSON ARRAY. No conversational filler.
    """

    advice = []
    
    # 3. Call OpenRouter
    logger.error("🔥 Smart Advice API HIT (OpenRouter)")
    
    try:
        model_name = "mistralai/mistral-7b-instruct:free"
        
        llm_response = await asyncio.wait_for(
            _call_openrouter(model_name, [{"role": "user", "content": prompt}]), 
            timeout=25.0 
        )
        
        # Guard against unavailable or empty responses
        if not llm_response or "unavailable" in str(llm_response).lower() or llm_response == "null":
            raise Exception("LLM response unavailable")
            
        cleaned = llm_response.replace("```json", "").replace("```", "").strip()
        
        # Extract JSON array safely
        start = cleaned.find('[')
        end = cleaned.rfind(']') + 1
        if start != -1 and end > start:
            cleaned = cleaned[start:end]
        
        parsed_advice = json.loads(cleaned)
        
        if isinstance(parsed_advice, list) and len(parsed_advice) > 0:
            valid_icons = ["shield", "trending-up", "landmark", "wallet", "zap", "activity", "target"]
            for item in parsed_advice:
                item["icon"] = item.get("icon") if item.get("icon") in valid_icons else "zap"
                item["label"] = item.get("label", "ADVICE").upper()
                item["title"] = item.get("title", "Insight").replace("**", "").strip()
                item["body"] = item.get("body", "").replace("**", "").strip()
                item["href"] = item.get("href", "/")
                item["action"] = item.get("action", "Explore")
            advice = parsed_advice
    except Exception as e:
        logger.error(f"❌ AI Advisory failed: {e}")

    # 4. Fallback Logic
    if not advice:
        advice = [
            {"icon": "trending-up", "label": "SPENDING", "title": "Budget Optimization", "body": f"You've spent ₹{expenses} this month. Review your {top_category} costs to save more.", "href": "/budget", "action": "View Budget"},
            {"icon": "shield", "label": "SAFETY", "title": "Emergency Fund", "body": "Aim for 3-6 months of expenses in a high-yield account.", "href": "/goals", "action": "Track Goals"},
            {"icon": "landmark", "label": "WEALTH", "title": "Net Worth Growth", "body": "Automate 10% of your income into investments to build long-term wealth.", "href": "/wallet", "action": "Manage Assets"},
            {"icon": "zap", "label": "ACTION", "title": "Smart Tracking", "body": "Review your weekly trends to identify hidden spending leaks early.", "href": "/transactions", "action": "See Trends"}
        ]

    return {
        "recommended_savings": round(max(income * 0.2, savings * 0.35), 2),
        "advice": advice,
        "behavior_profile": behavior_profile.get("behavior_profile", "balanced") if behavior_profile else "balanced",
    }
