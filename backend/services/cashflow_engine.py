from __future__ import annotations

from datetime import date, datetime, timedelta
import pandas as pd


def _safe_date(value: str, fallback_days: int = 7) -> str:
    try:
        return datetime.fromisoformat(str(value)).date().isoformat()
    except ValueError:
        return (date.today() + timedelta(days=fallback_days)).isoformat()


def build_cashflow_timeline(subscriptions: list[dict], emi_summary: dict, bills: list[dict], transactions=None) -> dict:
    upcoming: list[dict] = []

    for subscription in subscriptions:
        upcoming.append(
            {
                "name": subscription["name"],
                "date": _safe_date(subscription["next_due_date"], 14),
                "amount": round(float(subscription["monthly_cost"]), 2),
                "type": "Subscription",
            }
        )

    for emi in emi_summary.get("items", []):
        upcoming.append(
            {
                "name": emi["name"],
                "date": _safe_date(emi["due_date"], 10),
                "amount": round(float(emi["monthly_emi"]), 2),
                "type": "EMI",
            }
        )

    for index, bill in enumerate(bills):
        upcoming.append(
            {
                "name": bill["name"],
                "date": (date.today() + timedelta(days=index + 1)).isoformat(),
                "amount": round(float(bill["amount"]), 2),
                "type": "Bill",
            }
        )
        
    if transactions is not None and not transactions.empty:
        df = transactions.copy()
        df["date"] = pd.to_datetime(df["date"], errors="coerce")
        df = df.dropna(subset=["date"])
        expenses = df[df["amount"] < 0].copy()
        expenses["amount"] = expenses["amount"].abs()
        # Find transactions from last month to project to this month
        one_month_ago = date.today() - timedelta(days=30)
        recent_expenses = expenses[expenses["date"].dt.date >= one_month_ago]
        
        # We group by merchant to find regular occurrences
        merchant_counts = recent_expenses.groupby("merchant").size()
        frequent_merchants = merchant_counts[merchant_counts >= 2].index
        
        existing_names = {item["name"].lower() for item in upcoming}
        
        for merchant in frequent_merchants:
            if merchant.lower() in existing_names:
                continue
            merchant_tx = recent_expenses[recent_expenses["merchant"] == merchant]
            avg_amount = merchant_tx["amount"].mean()
            last_date = merchant_tx["date"].max().date()
            predicted_date = last_date + timedelta(days=30)
            
            if predicted_date >= date.today():
                upcoming.append({
                    "name": f"{merchant} (Predicted)",
                    "date": predicted_date.isoformat(),
                    "amount": round(avg_amount, 2),
                    "type": "Predicted Expense",
                })
                existing_names.add(merchant.lower())

    upcoming.sort(key=lambda item: item["date"])
    projection = round(sum(item["amount"] for item in upcoming), 2)
    return {
        "upcoming_payments": upcoming[:8],
        "monthly_outflow_projection": projection,
    }

