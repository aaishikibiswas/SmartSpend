from __future__ import annotations

from collections.abc import Iterable

import pandas as pd


FIXED_CATEGORIES = {"Rent", "EMI", "Subscription", "Bills", "Utilities", "Housing", "Insurance"}
VARIABLE_CATEGORIES = {"Food", "Shopping", "Transport", "Entertainment", "Other", "Healthcare", "Travel"}


def classify_expense(category: str) -> str:
    normalized = str(category or "").strip().title()
    if normalized in FIXED_CATEGORIES:
        return "fixed"
    return "variable"


def _iter_expense_rows(transactions: pd.DataFrame | Iterable[dict]) -> list[dict]:
    if isinstance(transactions, pd.DataFrame):
      if transactions.empty:
          return []
      rows = transactions.to_dict(orient="records")
    else:
      rows = list(transactions)

    normalized: list[dict] = []
    for txn in rows:
        amount = float(txn.get("amount", 0))
        txn_type = str(txn.get("type", "")).lower()
        is_expense = amount < 0 or txn_type in {"debit", "expense"}
        if not is_expense:
            continue
        normalized.append(
            {
                **txn,
                "amount": abs(amount),
                "category": str(txn.get("category", "Other")).title(),
            }
        )
    return normalized


def compute_expense_split(transactions: pd.DataFrame | Iterable[dict]) -> dict:
    fixed_total = 0.0
    variable_total = 0.0

    for txn in _iter_expense_rows(transactions):
        if classify_expense(txn["category"]) == "fixed":
            fixed_total += float(txn["amount"])
        else:
            variable_total += float(txn["amount"])

    total = fixed_total + variable_total
    return {
        "fixed_total": round(fixed_total, 2),
        "variable_total": round(variable_total, 2),
        "fixed_percent": round((fixed_total / total) * 100, 2) if total else 0.0,
        "variable_percent": round((variable_total / total) * 100, 2) if total else 0.0,
        "breakdown": [
            {"name": "Fixed", "amount": round(fixed_total, 2)},
            {"name": "Variable", "amount": round(variable_total, 2)},
        ],
    }


def classify_expense_split(transactions_df: pd.DataFrame, subscriptions: list[dict], emi_summary: dict, bills: list[dict]) -> dict:
    base = compute_expense_split(transactions_df)
    fixed_total = float(base["fixed_total"])
    variable_total = float(base["variable_total"])

    fixed_total += sum(float(item.get("monthly_cost", 0)) for item in subscriptions)
    fixed_total += float(emi_summary.get("monthly_load", 0))
    fixed_total += sum(float(item.get("amount", 0)) for item in bills)

    total = fixed_total + variable_total
    return {
        "fixed_total": round(fixed_total, 2),
        "variable_total": round(variable_total, 2),
        "fixed_percent": round((fixed_total / total) * 100, 2) if total else 0.0,
        "variable_percent": round((variable_total / total) * 100, 2) if total else 0.0,
        "breakdown": [
            {"name": "Fixed", "amount": round(fixed_total, 2)},
            {"name": "Variable", "amount": round(variable_total, 2)},
        ],
    }
