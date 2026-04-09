from __future__ import annotations

from typing import Any

import pandas as pd

from backend.services.emi_engine import summarize_emis
from backend.services.expense_classifier import classify_expense_split
from backend.services.subscription_engine import get_all_subscriptions
from backend.storage import Storage
from backend.storage import bills_db


DEFAULT_CATEGORY_TARGETS = {
    "Food": 0.24,
    "Transport": 0.14,
    "Shopping": 0.12,
    "Housing": 0.26,
    "Entertainment": 0.1,
    "Healthcare": 0.07,
    "Other": 0.07,
}


def _normalize_frequency(frequency: str | None) -> str:
    return "Weekly" if str(frequency or "").strip().lower() == "weekly" else "Monthly"


def _monthly_equivalent(amount: float, frequency: str) -> float:
    return float(amount) * 4.33 if _normalize_frequency(frequency) == "Weekly" else float(amount)


def _expenses_frame(transactions_df: pd.DataFrame | None = None) -> pd.DataFrame:
    df = transactions_df if transactions_df is not None else Storage.get_transactions()
    if df.empty:
        return pd.DataFrame(columns=["date", "merchant", "category", "amount", "type", "language"])
    expenses = df[df["amount"] < 0].copy()
    if expenses.empty:
        return pd.DataFrame(columns=df.columns)
    expenses["spend"] = expenses["amount"].abs()
    return expenses


def _category_spend(expenses_df: pd.DataFrame) -> dict[str, float]:
    if expenses_df.empty:
        return {}
    return (
        expenses_df.groupby("category")["spend"]
        .sum()
        .sort_values(ascending=False)
        .astype(float)
        .to_dict()
    )


def _usage_tone(usage_percent: float) -> str:
    if usage_percent >= 100:
        return "error"
    if usage_percent >= 80:
        return "warning"
    return "healthy"


def _summarize_category(name: str, amount: float, frequency: str, spent_lookup: dict[str, float]) -> dict[str, Any]:
    monthly_budget = _monthly_equivalent(amount, frequency)
    spent = round(float(spent_lookup.get(name, 0.0)), 2)
    remaining = round(monthly_budget - spent, 2)
    usage_percent = round((spent / monthly_budget) * 100, 2) if monthly_budget > 0 else 0.0
    return {
        "name": name,
        "allocated_amount": round(float(amount), 2),
        "frequency": _normalize_frequency(frequency),
        "spent_amount": spent,
        "remaining_amount": remaining,
        "usage_percent": usage_percent,
        "status": _usage_tone(usage_percent),
        "monthly_equivalent": round(monthly_budget, 2),
    }


def suggest_daily_allowance(monthly_remaining: float) -> float:
    return round(float(monthly_remaining) / 30, 2)


def get_category_budget_summary(transactions_df: pd.DataFrame | None = None) -> list[dict[str, Any]]:
    config = Storage.get_budget_config()
    expenses = _expenses_frame(transactions_df)
    spent_lookup = _category_spend(expenses)

    categories = [
        _summarize_category(name, value["amount"], value["frequency"], spent_lookup)
        for name, value in config["categories"].items()
    ]
    categories.sort(key=lambda item: (-item["usage_percent"], item["name"]))
    return categories


def get_global_budget_summary(transactions_df: pd.DataFrame | None = None) -> dict[str, Any]:
    config = Storage.get_budget_config()
    expenses = _expenses_frame(transactions_df)
    total_spent = round(float(expenses["spend"].sum()), 2) if not expenses.empty else 0.0
    monthly_budget = float(config["monthly"])
    subscriptions = get_all_subscriptions(transactions_df if transactions_df is not None else Storage.get_transactions())
    emi_summary = summarize_emis(transactions_df)
    expense_split = classify_expense_split(transactions_df if transactions_df is not None else Storage.get_transactions(), subscriptions, emi_summary, bills_db)
    fixed_reserved = round(float(expense_split["fixed_total"]), 2)
    adjustable_variable_budget = max(monthly_budget - fixed_reserved, 0.0)
    remaining = round(monthly_budget - total_spent - fixed_reserved, 2)
    usage_percent = round((total_spent / monthly_budget) * 100, 2) if monthly_budget > 0 else 0.0

    return {
        "monthly_budget": round(monthly_budget, 2),
        "weekly_budget": round(float(config["weekly"]), 2),
        "spent_amount": total_spent,
        "remaining_amount": remaining,
        "usage_percent": usage_percent,
        "daily_allowance": suggest_daily_allowance(remaining),
        "fixed_reserved": fixed_reserved,
        "adjustable_variable_budget": round(adjustable_variable_budget, 2),
        "auto_distribute": bool(config.get("auto_distribute", False)),
        "status": _usage_tone(usage_percent),
    }


def auto_distribute_category_budgets(monthly_budget: float, transactions_df: pd.DataFrame | None = None) -> dict[str, dict[str, Any]]:
    expenses = _expenses_frame(transactions_df)
    spend_lookup = _category_spend(expenses)
    spend_lookup = {name: value for name, value in spend_lookup.items() if name not in {"Rent", "EMI", "Subscription", "Bills", "Utilities"}}
    categories = spend_lookup or DEFAULT_CATEGORY_TARGETS

    if spend_lookup:
        total_spend = sum(spend_lookup.values()) or 1.0
        weights = {name: value / total_spend for name, value in spend_lookup.items()}
    else:
        weights = DEFAULT_CATEGORY_TARGETS

    allocation = {}
    for name, ratio in weights.items():
        allocation[name] = {
            "amount": round(float(monthly_budget) * float(ratio), 2),
            "frequency": "Monthly",
        }
    return allocation


def set_global_budget(monthly_budget: float, auto_distribute: bool = False, transactions_df: pd.DataFrame | None = None) -> dict[str, Any]:
    monthly_budget = max(0.0, float(monthly_budget))
    weekly_budget = round(monthly_budget / 4.33, 2)
    config = Storage.get_budget_config()
    categories = config["categories"]

    if auto_distribute:
        categories = auto_distribute_category_budgets(monthly_budget, transactions_df)

    Storage.update_budget_config(
        {
            "monthly": monthly_budget,
            "weekly": weekly_budget,
            "auto_distribute": auto_distribute,
            "categories": categories,
        }
    )
    return get_global_budget_summary(transactions_df)


def add_or_update_category_budget(name: str, amount: float, frequency: str, transactions_df: pd.DataFrame | None = None) -> dict[str, Any]:
    config = Storage.get_budget_config()
    categories = dict(config["categories"])
    categories[str(name).strip()] = {
        "amount": round(max(0.0, float(amount)), 2),
        "frequency": _normalize_frequency(frequency),
    }

    Storage.update_budget_config(
        {
            "monthly": config["monthly"],
            "weekly": config["weekly"],
            "auto_distribute": config.get("auto_distribute", False),
            "categories": categories,
        }
    )

    updated = get_category_budget_summary(transactions_df)
    match = next((item for item in updated if item["name"] == str(name).strip()), None)
    return match or _summarize_category(str(name).strip(), amount, frequency, {})


def remove_category_budget(name: str, transactions_df: pd.DataFrame | None = None) -> list[dict[str, Any]]:
    config = Storage.get_budget_config()
    categories = dict(config["categories"])
    categories.pop(name, None)
    Storage.update_budget_config(
        {
            "monthly": config["monthly"],
            "weekly": config["weekly"],
            "auto_distribute": config.get("auto_distribute", False),
            "categories": categories,
        }
    )
    return get_category_budget_summary(transactions_df)


def build_budget_feedback(transactions_df: pd.DataFrame | None = None) -> list[str]:
    global_summary = get_global_budget_summary(transactions_df)
    category_summary = get_category_budget_summary(transactions_df)
    feedback: list[str] = []

    if global_summary["remaining_amount"] >= 0:
        feedback.append(f"You have Rs{round(global_summary['remaining_amount']):,} left this month.")
        feedback.append(f"Your daily spending allowance is Rs{round(global_summary['daily_allowance']):,}.")
    else:
        feedback.append(f"You are over budget by Rs{round(abs(global_summary['remaining_amount'])):,} this month.")

    over_category = next((item for item in category_summary if item["usage_percent"] >= 100), None)
    near_category = next((item for item in category_summary if 80 <= item["usage_percent"] < 100), None)

    if over_category:
        feedback.append(f"You are overspending in {over_category['name']} by Rs{round(abs(over_category['remaining_amount'])):,}.")
    elif near_category:
        feedback.append(f"{near_category['name']} is already at {round(near_category['usage_percent'])}% of budget.")

    return feedback[:3]


def build_budget_snapshot(transactions_df: pd.DataFrame | None = None) -> dict[str, Any]:
    return {
        "global": get_global_budget_summary(transactions_df),
        "categories": get_category_budget_summary(transactions_df),
        "feedback": build_budget_feedback(transactions_df),
    }


def get_budget_snapshot(transactions_df: pd.DataFrame | None = None) -> dict[str, Any]:
    return build_budget_snapshot(transactions_df)


def sync_budget_with_transactions(transactions_df: pd.DataFrame | None = None) -> None:
    config = Storage.get_budget_config()
    if config.get("auto_distribute"):
        set_global_budget(config["monthly"], True, transactions_df)
