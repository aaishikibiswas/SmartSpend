from __future__ import annotations

from typing import Any

from backend.models.predict import build_daily_expense_series, predict_next_expense
from backend.services.budget_engine import get_budget_snapshot
from backend.services.categorizer import categorize_transaction
from backend.services.emi_engine import summarize_emis
from backend.services.analytics import get_dashboard_analytics
from backend.services.expense_classifier import classify_expense_split
from backend.services.subscription_engine import get_all_subscriptions
from backend.storage import Storage, bills_db


def evaluate_purchase(item_name: str, price: float) -> dict[str, Any]:
    item_name = (item_name or "").strip()
    price = round(max(0.0, float(price)), 2)
    category = categorize_transaction(item_name, amount=price) if item_name else "Other"

    metrics = get_dashboard_analytics()
    transactions = Storage.get_transactions()
    budget_snapshot = get_budget_snapshot(transactions)
    prediction = predict_next_expense(build_daily_expense_series(transactions))
    emi_summary = summarize_emis()
    subscriptions = get_all_subscriptions(transactions)
    expense_split = classify_expense_split(transactions, subscriptions, emi_summary, bills_db)

    global_remaining = float(budget_snapshot["global"]["remaining_amount"])
    category_budget = next((item for item in budget_snapshot["categories"] if item["name"].lower() == category.lower()), None)
    category_remaining = float(category_budget["remaining_amount"]) if category_budget else global_remaining
    current_risk = prediction["risk_level"]

    post_global_remaining = global_remaining - price
    post_category_remaining = category_remaining - price
    budget_impact_pct = round((price / max(float(budget_snapshot["global"]["monthly_budget"]), 1.0)) * 100, 2)
    recurring_load = float(emi_summary["monthly_load"]) + sum(float(item["monthly_cost"]) for item in subscriptions)
    affordability_buffer = float(metrics["netSavings"]) - recurring_load
    variable_remaining = max(float(budget_snapshot["global"].get("adjustable_variable_budget", 0)) - float(expense_split["variable_total"]), 0.0)

    if post_global_remaining < 0 or post_category_remaining < 0 or affordability_buffer <= 0 or variable_remaining < price:
        affordability = "No"
        status = "error"
        recommendation = f"Do not buy {item_name or 'this item'} now. It would strain your variable spending capacity after fixed commitments."
        new_risk = "High"
    elif current_risk == "High" or post_global_remaining < prediction["predicted_expense"]:
        affordability = "Maybe"
        status = "warning"
        recommendation = f"You can buy {item_name or 'this item'}, but it is risky. Wait or reduce spending in {category} first."
        new_risk = "High"
    elif budget_impact_pct >= 20:
        affordability = "Maybe"
        status = "warning"
        recommendation = f"This purchase is affordable, but it consumes {budget_impact_pct}% of your monthly budget."
        new_risk = "Medium"
    else:
        affordability = "Yes"
        status = "success"
        recommendation = f"Yes, you can afford {item_name or 'this purchase'} and stay within your current budget plan."
        new_risk = "Medium" if current_risk == "Low" and budget_impact_pct > 10 else current_risk

    return {
        "item_name": item_name,
        "category": category,
        "price": price,
        "affordability": affordability,
        "status": status,
        "budget_impact_percent": budget_impact_pct,
        "current_risk_level": current_risk,
        "new_risk_level": new_risk,
        "remaining_global_budget": round(post_global_remaining, 2),
        "remaining_category_budget": round(post_category_remaining, 2),
        "recommendation": recommendation,
    }
