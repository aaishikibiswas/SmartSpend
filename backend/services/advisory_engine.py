from __future__ import annotations
import asyncio
import json
import logging
import random
from backend.services.llm_client import _call_openrouter, PRIMARY_MODEL

logger = logging.getLogger("smartspend.advisory")

GENERAL_ADVICE_POOL = [
    {"icon": "shield", "label": "SECURITY", "title": "Emergency Fund", "body": "Maintain 3-6 months of expenses in a liquid account for unexpected events.", "href": "/goals", "action": "Check Goals"},
    {"icon": "trending-up", "label": "WEALTH", "title": "Compound Interest", "body": "Starting early is more important than the amount. Let time do the heavy lifting.", "href": "/wallet", "action": "Invest Now"},
    {"icon": "landmark", "label": "TAX", "title": "Tax Planning", "body": "Review your 80C investments before the quarter ends to maximize tax savings.", "href": "/wallet", "action": "Tax Assets"},
    {"icon": "wallet", "label": "BUDGET", "title": "50/30/20 Rule", "body": "Aim to spend 50% on needs, 30% on wants, and save 20% of your income.", "href": "/budget", "action": "View Rule"},
    {"icon": "zap", "label": "ACTION", "title": "Weekly Review", "body": "Spend 5 minutes every Sunday reviewing your transactions to stay on track.", "href": "/transactions", "action": "Review Tx"},
    {"icon": "target", "label": "GOALS", "title": "Automate Savings", "body": "Set up a standing instruction to move money to savings on your salary date.", "href": "/goals", "action": "Set Auto-Pay"},
    {"icon": "activity", "label": "HEALTH", "title": "Credit Utilization", "body": "Keep your credit card usage below 30% to maintain a healthy credit score.", "href": "/wallet", "action": "Check Credit"},
    {"icon": "shield", "label": "SAFETY", "title": "Insurance Coverage", "body": "Ensure your term and health insurance covers at least 10x your annual income.", "href": "/goals", "action": "Plan Safety"},
    {"icon": "trending-up", "label": "SPENDING", "title": "Avoid Lifestyle Creep", "body": "When your income increases, keep your expenses same for at least 6 months.", "href": "/budget", "action": "Limit Spends"},
    {"icon": "zap", "label": "QUICK TIP", "title": "Subscription Audit", "body": "Cancel at least one unused subscription today to save an average of ₹500/mo.", "href": "/transactions", "action": "Audit Now"}
]

import re

async def generate_financial_advice(metrics: dict, budget_snapshot: dict, prediction: dict, expense_split: dict, behavior_profile: dict | None = None) -> dict:
    """
    REBUILT: Hybrid Smart Advice system.
    Combines Real-time Rules + AI Insights + General Wisdom.
    """
    try:
        # 1. Summarize Financial Data
        income = float(metrics.get("totalIncome", 0))
        expenses = float(metrics.get("totalExpense", 0))
        savings = float(metrics.get("netSavings", 0))
        savings_rate = float(metrics.get("savingsRatio", 0))
        
        global_budget = budget_snapshot.get("global", {})
        rem_amount = float(global_budget.get("remaining_amount", 0))
        daily_allowance = float(global_budget.get("daily_allowance", 0))
        budget_usage = float(global_budget.get("usage_percent", 0))
        
        categories = budget_snapshot.get("categories", [])
        top_cat_item = max(categories, key=lambda x: x.get("spent_amount", 0)) if categories else {"name": "None", "spent_amount": 0}
        top_category = top_cat_item.get("name", "General")
        
        recurring_total = float(metrics.get("subscriptionLoad", 0)) + float(metrics.get("monthlyEmiLoad", 0))

        final_advice = []

        # 2. Rule-Based Real-Time Insights (Guaranteed variety)
        if rem_amount < 0:
            final_advice.append({
                "icon": "zap", "label": "BUDGET", "title": "Over-Budget Alert", 
                "body": f"You are ₹{round(abs(rem_amount))} over your planned budget. Try to limit non-essential spending.", 
                "href": "/budget", "action": "Fix Budget"
            })
        elif budget_usage > 80:
            final_advice.append({
                "icon": "activity", "label": "WARNING", "title": "Budget Near Limit", 
                "body": f"You've used {budget_usage}% of your budget with {30 - max(1, int(metrics.get('day_of_month', 15)))} days left.", 
                "href": "/budget", "action": "Review Limits"
            })
        elif daily_allowance > 0:
             final_advice.append({
                "icon": "wallet", "label": "ALLOWANCE", "title": "Daily Spend Target", 
                "body": f"To stay within budget, aim to spend no more than ₹{round(daily_allowance)} per day for the rest of the month.", 
                "href": "/transactions", "action": "View Spends"
            })

        if savings_rate > 30:
            final_advice.append({
                "icon": "target", "label": "EXCELLENT", "title": "High Savings Mode", 
                "body": f"Your {savings_rate}% savings rate is in the top 5% of users. Consider investing the surplus.", 
                "href": "/wallet", "action": "Grow Wealth"
            })

        over_cats = [c for c in categories if c.get("usage_percent", 0) > 95]
        if over_cats:
            cat = over_cats[0]
            final_advice.append({
                "icon": "zap", "label": "CATEGORY", "title": f"{cat['name']} Limit Reached", 
                "body": f"You've exhausted your {cat['name']} budget. Any more spends will affect your net savings.", 
                "href": "/budget", "action": "Adjust Category"
            })

        if recurring_total > income * 0.25:
             final_advice.append({
                "icon": "activity", "label": "FIXED COSTS", "title": "High Monthly Load", 
                "body": f"₹{recurring_total} is locked in EMIs/Bills. Avoid taking new commitments this month.", 
                "href": "/transactions", "action": "Check Bills"
            })

        # 3. AI-Generated Advice
        prompt = f"""Act as a senior financial advisor.
        Context: Income ₹{income}, Expenses ₹{expenses}, Savings ₹{savings} ({savings_rate}%), Top: {top_category}, Recurring: ₹{recurring_total}.
        Generate 3-4 highly personalized advice items as JSON array. 
        NO conversational text. NO preamble. ONLY THE JSON ARRAY.
        Icons: ["shield", "trending-up", "landmark", "wallet", "zap", "activity", "target"].
        Routes: ["/budget", "/transactions", "/wallet", "/alerts", "/goals", "/"].
        """

        async def try_ai_generation(model):
            try:
                logger.info(f"Smart Advice: Attempting AI insights with {model}...")
                resp = await asyncio.wait_for(
                    _call_openrouter(model, [{"role": "user", "content": prompt}]), 
                    timeout=20.0 
                )
                if resp and "unavailable" not in str(resp).lower() and resp != "null":
                    match = re.search(r'\[\s*\{.*\}\s*\]', resp, re.DOTALL)
                    if match:
                        return json.loads(match.group(0))
            except Exception as e:
                logger.warning(f"Smart Advice: {model} failed: {type(e).__name__}")
            return None

        # Try models in order
        ai_items = await try_ai_generation(PRIMARY_MODEL)
        if not ai_items:
            ai_items = await try_ai_generation(FALLBACK_MODEL)
        
        if ai_items and isinstance(ai_items, list):
            valid_items = [i for i in ai_items if isinstance(i, dict)]
            final_advice.extend(valid_items[:4])
        else:
            logger.error("❌ AI Advisory: All models failed or returned no valid items.")

        # 4. Fill with General Advice Pool
        needed = 12 - len(final_advice)
        if needed > 0:
            pool_sample = random.sample(GENERAL_ADVICE_POOL, min(needed, len(GENERAL_ADVICE_POOL)))
            final_advice.extend(pool_sample)

        # 5. Clean & Sanitize
        valid_icons = ["shield", "trending-up", "landmark", "wallet", "zap", "activity", "target"]
        sanitized = []
        for item in final_advice:
            if not isinstance(item, dict):
                continue
            
            title = str(item.get("title", "")).replace("**", "").strip()[:40]
            body = str(item.get("body", "")).replace("**", "").strip()[:140]
            
            # Only include if it has actual content
            if not title or not body:
                continue

            sanitized.append({
                "icon": item.get("icon") if item.get("icon") in valid_icons else "zap",
                "label": str(item.get("label", "ADVICE")).upper()[:12],
                "title": title,
                "body": body,
                "href": str(item.get("href", "/")),
                "action": str(item.get("action", "Explore"))[:15]
            })

        # If too many were filtered, top up with general pool to ensure variety
        if len(sanitized) < 12:
            pool_needed = 12 - len(sanitized)
            # Sample from pool, but don't duplicate items already in sanitized
            pool_titles = {s["title"] for s in sanitized}
            available_pool = [p for p in GENERAL_ADVICE_POOL if p["title"] not in pool_titles]
            
            pool_sample = random.sample(available_pool, min(pool_needed, len(available_pool)))
            for p in pool_sample:
                sanitized.append(p)

        random.shuffle(sanitized)

        return {
            "recommended_savings": round(max(income * 0.2, savings * 0.35), 2),
            "advice": sanitized,
            "behavior_profile": behavior_profile.get("behavior_profile", "balanced") if (behavior_profile and isinstance(behavior_profile, dict)) else "balanced",
        }
    except Exception as e:
        logger.error(f"❌ FATAL Advisory Engine Error: {type(e).__name__}: {e}")
        # absolute safety fallback
        return {
            "recommended_savings": 0,
            "advice": random.sample(GENERAL_ADVICE_POOL, 8),
            "behavior_profile": "balanced"
        }



