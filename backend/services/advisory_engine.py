from __future__ import annotations
import asyncio
from backend.services.llm_client import _call_openrouter

async def generate_financial_advice(metrics: dict, budget_snapshot: dict, prediction: dict, expense_split: dict, behavior_profile: dict | None = None) -> dict:
    recommended_savings = round(max(float(metrics.get("totalIncome", 0)) * 0.2, float(metrics.get("netSavings", 0)) * 0.35), 2)
    allocation = {
        "essentials": round(min(55.0, max(float(expense_split.get("fixed_percent", 0)), 35.0)), 2),
        "flexible": round(max(15.0, min(float(expense_split.get("variable_percent", 0)), 35.0)), 2),
        "savings": round(max(10.0, min(100.0, (recommended_savings / max(float(metrics.get("totalIncome", 1)), 1)) * 100)), 2),
    }
    advice = []

    if float(prediction.get("confidence_score", 0)) < 0.45:
        advice.append({
            "title": "Prediction confidence is moderate",
            "body": "Keep a larger cash buffer before discretionary spending due to unpredictable patterns.",
            "action": "View Wallet",
            "href": "/wallet",
            "label": "Security",
            "icon": "shield"
        })
    if float(metrics.get("savingsRatio", 0)) < 20:
        advice.append({
            "title": f"Low savings ratio ({float(metrics.get('savingsRatio', 0))}%)",
            "body": "Increase automated savings contributions before adding new recurring expenses.",
            "action": "Set Goals",
            "href": "/goals",
            "label": "Investment",
            "icon": "trending-up"
        })
    if float(expense_split.get("fixed_percent", 0)) > 65:
        advice.append({
            "title": f"Fixed commitments at {float(expense_split.get('fixed_percent', 0))}%",
            "body": "Review subscriptions, EMIs, and utilities first before more spending.",
            "action": "Review Subscriptions",
            "href": "/transactions",
            "label": "Efficiency",
            "icon": "landmark"
        })
    if float(budget_snapshot["global"].get("usage_percent", 0)) > 80:
        advice.append({
            "title": f"High budget utilization ({float(budget_snapshot['global'].get('usage_percent', 0))}%)",
            "body": "Reduce variable spending until the next cycle to avoid breaching.",
            "action": "Go to Budget",
            "href": "/budget",
            "label": "Budgeting",
            "icon": "landmark"
        })
    if behavior_profile:
        if behavior_profile.get("behavior_profile") == "high fixed burden":
            advice.append({
                "title": "High Fixed Burden detected",
                "body": "Prioritize renegotiating fixed commitments before lifestyle upgrades.",
                "action": "Manage Bills",
                "href": "/transactions",
                "label": "Efficiency",
                "icon": "shield"
            })
        elif behavior_profile.get("behavior_profile") == "high variable spending":
            advice.append({
                "title": "High Variable Spending",
                "body": "Use stricter discretionary controls this cycle.",
                "action": "Adjust Budgets",
                "href": "/budget",
                "label": "Budgeting",
                "icon": "trending-up"
            })
            
    # Generate generic LLM advice if configured
    try:
        prompt = f"User has income {metrics.get('totalIncome')}, savings {metrics.get('netSavings')}, and usage {budget_snapshot['global'].get('usage_percent')}%. Give 1 short, 1-sentence financial tip based on this."
        llm_response = await asyncio.wait_for(_call_openrouter("mistralai/mistral-7b-instruct", [{"role": "user", "content": prompt}]), timeout=5.0)
        if llm_response and "unavailable" not in llm_response.lower():
            advice.insert(0, {
                "title": "AI Insight",
                "body": llm_response[:100] + ("..." if len(llm_response) > 100 else ""),
                "action": "Ask AI",
                "href": "/#ai-chat",
                "label": "General",
                "icon": "lightbulb"
            })
    except Exception:
        pass

    if not advice:
        advice.append({
            "title": "Spending pattern is balanced",
            "body": "Continue prioritizing savings and keep discretionary expenses within budget.",
            "action": "View Goals",
            "href": "/goals",
            "label": "Efficiency",
            "icon": "landmark"
        })

    return {
        "recommended_savings": recommended_savings,
        "budget_allocation": allocation,
        "advice": advice[:3],
        "behavior_profile": behavior_profile.get("behavior_profile", "balanced") if behavior_profile else "balanced",
    }
