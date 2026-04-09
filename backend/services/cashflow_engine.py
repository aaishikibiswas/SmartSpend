from __future__ import annotations

from datetime import date, datetime, timedelta


def _safe_date(value: str, fallback_days: int = 7) -> str:
    try:
        return datetime.fromisoformat(str(value)).date().isoformat()
    except ValueError:
        return (date.today() + timedelta(days=fallback_days)).isoformat()


def build_cashflow_timeline(subscriptions: list[dict], emi_summary: dict, bills: list[dict]) -> dict:
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

    upcoming.sort(key=lambda item: item["date"])
    projection = round(sum(item["amount"] for item in upcoming if item["type"] in {"Subscription", "EMI", "Bill"}), 2)
    return {
        "upcoming_payments": upcoming[:8],
        "monthly_outflow_projection": projection,
    }

