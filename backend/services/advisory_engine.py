from __future__ import annotations

import asyncio
import json
import logging
import random
import re

from backend.services.llm_client import (
    FALLBACK_MODEL,
    PRIMARY_MODEL,
    SECONDARY_FALLBACK,
    _call_openrouter,
)

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
    {"icon": "zap", "label": "QUICK TIP", "title": "Subscription Audit", "body": "Cancel at least one unused subscription today to save an average of Rs500/mo.", "href": "/transactions", "action": "Audit Now"},
]


def _money(value: float) -> str:
    return f"Rs{round(float(value or 0)):,}"


def _contextual_rule_advice(
    income: float,
    expenses: float,
    savings: float,
    savings_rate: float,
    rem_amount: float,
    daily_allowance: float,
    budget_usage: float,
    recurring_total: float,
    categories: list,
    prediction: dict,
    expense_split: dict,
    behavior_profile: dict | None,
) -> list[dict]:
    """Create live advice from dashboard numbers, independent of the remote LLM."""
    items: list[dict] = []
    day_of_month = max(1, min(31, int((behavior_profile or {}).get("day_of_month", 15) or 15)))
    days_left = max(0, 30 - day_of_month)
    top_categories = sorted(categories, key=lambda x: float(x.get("spent_amount", x.get("amount", 0)) or 0), reverse=True)[:3]
    top_category = top_categories[0] if top_categories else None
    next_expense = prediction.get("next_expense_prediction", {}) if isinstance(prediction, dict) else {}
    predicted_expense = float(next_expense.get("predicted_expense", 0) or 0)
    risk_level = str(next_expense.get("risk_level", "") or "").lower()
    fixed_percent = float(expense_split.get("fixed_percent", 0) or 0) if isinstance(expense_split, dict) else 0
    variable_total = float(expense_split.get("variable_total", 0) or 0) if isinstance(expense_split, dict) else 0
    behavior = str((behavior_profile or {}).get("behavior_profile", "balanced")).replace("_", " ").title()

    if income <= 0 and expenses <= 0:
        return [{
            "icon": "wallet",
            "label": "SETUP",
            "title": "Add Fresh Transactions",
            "body": "Upload or add this month's transactions so Smart Insights can calculate real budget pressure and savings moves.",
            "href": "/upload",
            "action": "Upload Data",
        }]

    if rem_amount < 0:
        items.append({
            "icon": "zap",
            "label": "BUDGET",
            "title": "Recover Budget Breach",
            "body": f"You are {_money(abs(rem_amount))} over budget. Freeze flexible spends until income or budget limits catch up.",
            "href": "/budget",
            "action": "Fix Budget",
        })
    elif budget_usage >= 80:
        items.append({
            "icon": "activity",
            "label": "WARNING",
            "title": "Budget Near Limit",
            "body": f"You have used {round(budget_usage)}% of budget with {days_left} days left. Use only priority spends this week.",
            "href": "/budget",
            "action": "Review Limits",
        })
    elif daily_allowance > 0:
        items.append({
            "icon": "wallet",
            "label": "TODAY",
            "title": "Daily Spend Ceiling",
            "body": f"Keep today's discretionary spend near {_money(daily_allowance)} to finish the month inside your plan.",
            "href": "/transactions",
            "action": "Track Today",
        })

    if savings_rate < 10 and income > 0:
        daily_trim = max(500, round((income * 0.15 - max(savings, 0)) / max(days_left, 1)))
        items.append({
            "icon": "target",
            "label": "SAVINGS",
            "title": "Savings Ratio Is Thin",
            "body": f"Your savings rate is {round(savings_rate, 1)}%. Cutting about {_money(daily_trim)} per day can move you toward a 15% buffer.",
            "href": "/goals",
            "action": "Set Target",
        })
    elif savings_rate >= 25:
        investable = max(0, savings - income * 0.2)
        items.append({
            "icon": "trending-up",
            "label": "WEALTH",
            "title": "Surplus Can Work Harder",
            "body": f"After protecting a 20% cash buffer, around {_money(investable)} may be available for goals or investments.",
            "href": "/wallet",
            "action": "Allocate",
        })

    if top_category:
        cat_name = str(top_category.get("name", "Top category"))
        cat_spend = float(top_category.get("spent_amount", top_category.get("amount", 0)) or 0)
        cat_usage = float(top_category.get("usage_percent", 0) or 0)
        if cat_usage >= 80:
            items.append({
                "icon": "activity",
                "label": "CATEGORY",
                "title": f"{cat_name} Needs Attention",
                "body": f"{cat_name} has used {round(cat_usage)}% of its limit. Cap it for {days_left} days to protect savings.",
                "href": "/budget",
                "action": "Tune Limit",
            })
        elif cat_spend > 0:
            items.append({
                "icon": "activity",
                "label": "SPEND MAP",
                "title": f"{cat_name} Leads Spending",
                "body": f"{cat_name} is your largest spend area at {_money(cat_spend)}. Review the last three transactions there first.",
                "href": "/transactions",
                "action": "Review",
            })

    if recurring_total > 0 and income > 0:
        recurring_ratio = recurring_total / income * 100
        if recurring_ratio >= 20:
            items.append({
                "icon": "shield",
                "label": "FIXED COST",
                "title": "Recurring Load Is Heavy",
                "body": f"EMIs and subscriptions take {round(recurring_ratio)}% of income. Avoid new monthly commitments this cycle.",
                "href": "/transactions",
                "action": "Audit Bills",
            })

    if fixed_percent >= 60:
        items.append({
            "icon": "landmark",
            "label": "CASHFLOW",
            "title": "Fixed Costs Dominate",
            "body": f"Fixed expenses are {round(fixed_percent)}% of outflow. Renegotiate bills before trimming small daily spends.",
            "href": "/transactions",
            "action": "Check Bills",
        })
    elif variable_total > 0:
        items.append({
            "icon": "zap",
            "label": "CONTROL",
            "title": "Variable Spend Lever",
            "body": f"Variable spending is {_money(variable_total)} this month. A 10% trim frees {_money(variable_total * 0.1)} quickly.",
            "href": "/budget",
            "action": "Trim 10%",
        })

    if predicted_expense > 0:
        label = "RISK" if risk_level in {"high", "critical"} else "FORECAST"
        items.append({
            "icon": "zap" if label == "RISK" else "trending-up",
            "label": label,
            "title": "Next Spend Forecast",
            "body": f"The model expects the next expense near {_money(predicted_expense)}. Keep it below today's allowance if possible.",
            "href": "/transactions",
            "action": "Plan Spend",
        })

    items.append({
        "icon": "shield",
        "label": "PROFILE",
        "title": f"{behavior} Pattern",
        "body": f"Your current behavior profile is {behavior.lower()}. Match limits to actual spend timing instead of a flat monthly rule.",
        "href": "/budget",
        "action": "Personalize",
    })

    return items


def _extract_json_array(response: str) -> list | None:
    if not response:
        return None

    try:
        parsed = json.loads(response)
        return parsed if isinstance(parsed, list) else None
    except json.JSONDecodeError:
        pass

    match = re.search(r"\[\s*\{.*\}\s*\]", response, re.DOTALL)
    if not match:
        return None

    try:
        parsed = json.loads(match.group(0))
        return parsed if isinstance(parsed, list) else None
    except json.JSONDecodeError:
        return None


async def generate_financial_advice(metrics: dict, budget_snapshot: dict, prediction: dict, expense_split: dict, behavior_profile: dict | None = None) -> dict:
    """
    Hybrid Smart Insights:
    - always derive live financial advice from dashboard data
    - optionally enrich it with OpenRouter model output when configured
    - avoid looping static evergreen tips unless there is no financial data
    """
    try:
        income = float(metrics.get("totalIncome", 0) or 0)
        expenses = float(metrics.get("totalExpense", 0) or 0)
        savings = float(metrics.get("netSavings", 0) or 0)
        savings_rate = float(metrics.get("savingsRatio", 0) or 0)

        global_budget = budget_snapshot.get("global", {}) if isinstance(budget_snapshot, dict) else {}
        rem_amount = float(global_budget.get("remaining_amount", metrics.get("remainingBudget", 0)) or 0)
        daily_allowance = float(global_budget.get("daily_allowance", metrics.get("dailyAllowance", 0)) or 0)
        budget_usage = float(global_budget.get("usage_percent", metrics.get("budgetUsagePercent", 0)) or 0)

        categories = budget_snapshot.get("categories", []) if isinstance(budget_snapshot, dict) else []
        top_cat_item = max(categories, key=lambda x: float(x.get("spent_amount", x.get("amount", 0)) or 0)) if categories else {"name": "General"}
        top_category = top_cat_item.get("name", "General")

        recurring_total = float(metrics.get("subscriptionLoad", 0) or 0) + float(metrics.get("monthlyEmiLoad", 0) or 0)
        final_advice = _contextual_rule_advice(
            income,
            expenses,
            savings,
            savings_rate,
            rem_amount,
            daily_allowance,
            budget_usage,
            recurring_total,
            categories,
            prediction,
            expense_split,
            behavior_profile,
        )

        prompt = f"""Act as a senior financial advisor for a personal finance dashboard.
Context: Income {_money(income)}, Expenses {_money(expenses)}, Savings {_money(savings)} ({savings_rate}%), Budget used {budget_usage}%, Remaining budget {_money(rem_amount)}, Daily allowance {_money(daily_allowance)}, Top category {top_category}, Recurring commitments {_money(recurring_total)}, Expense split {json.dumps(expense_split)}.
Generate 3 highly personalized advice items as JSON array.
Each item must have: icon, label, title, body, href, action.
NO conversational text. NO preamble. ONLY THE JSON ARRAY.
Icons: ["shield", "trending-up", "landmark", "wallet", "zap", "activity", "target"].
Routes: ["/budget", "/transactions", "/wallet", "/alerts", "/goals", "/"].
"""

        async def try_ai_generation(model: str) -> list | None:
            try:
                logger.info("Smart Advice: Attempting AI insights with %s", model)
                response = await asyncio.wait_for(
                    _call_openrouter(model, [{"role": "user", "content": prompt}]),
                    timeout=20.0,
                )
                return _extract_json_array(response)
            except Exception as exc:
                logger.warning("Smart Advice: %s failed: %s", model, type(exc).__name__)
                return None

        ai_items = None
        for model in (PRIMARY_MODEL, FALLBACK_MODEL, SECONDARY_FALLBACK):
            ai_items = await try_ai_generation(model)
            if ai_items:
                break

        if ai_items:
            final_advice.extend(item for item in ai_items[:3] if isinstance(item, dict))
        else:
            logger.warning("Smart Advice: OpenRouter did not return valid JSON; using live rule insights.")

        valid_icons = ["shield", "trending-up", "landmark", "wallet", "zap", "activity", "target"]
        sanitized: list[dict] = []
        seen_titles: set[str] = set()

        for item in final_advice:
            if not isinstance(item, dict):
                continue

            title = str(item.get("title", "")).replace("**", "").strip()[:44]
            body = str(item.get("body", "")).replace("**", "").strip()[:150]
            if not title or not body or title in seen_titles:
                continue

            href = str(item.get("href", "/"))
            if href not in ["/budget", "/transactions", "/wallet", "/alerts", "/goals", "/", "/upload"]:
                href = "/"

            sanitized.append({
                "icon": item.get("icon") if item.get("icon") in valid_icons else "zap",
                "label": str(item.get("label", "ADVICE")).upper()[:12],
                "title": title,
                "body": body,
                "href": href,
                "action": str(item.get("action", "Explore"))[:15],
            })
            seen_titles.add(title)

        if len(sanitized) < 3 and income <= 0 and expenses <= 0:
            available_pool = [item for item in GENERAL_ADVICE_POOL if item["title"] not in seen_titles]
            sanitized.extend(random.sample(available_pool, min(3 - len(sanitized), len(available_pool))))

        random.shuffle(sanitized)

        return {
            "recommended_savings": round(max(income * 0.2, savings * 0.35), 2),
            "advice": sanitized[:8],
            "behavior_profile": behavior_profile.get("behavior_profile", "balanced") if isinstance(behavior_profile, dict) else "balanced",
        }
    except Exception as exc:
        logger.error("Fatal advisory engine error: %s: %s", type(exc).__name__, exc)
        return {
            "recommended_savings": 0,
            "advice": random.sample(GENERAL_ADVICE_POOL, 3),
            "behavior_profile": "balanced",
        }
