from __future__ import annotations

from datetime import date, datetime

from backend.services.subscription_engine import detect_emi_transactions
from backend.storage import Storage


def _to_date(value: str) -> date | None:
    try:
        return datetime.fromisoformat(str(value)).date()
    except ValueError:
        return None


def get_manual_emis() -> list[dict]:
    return Storage.get_emis()


def get_all_emis(transactions_df=None) -> list[dict]:
    manual = [{**item, "source": item.get("source", "manual")} for item in get_manual_emis()]
    detected = detect_emi_transactions(transactions_df if transactions_df is not None else Storage.get_transactions())
    combined: list[dict] = []
    seen: set[str] = set()
    for item in [*manual, *detected]:
        key = str(item.get("name", "")).strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        combined.append(item)
    return combined


def add_emi(payload: dict) -> dict:
    normalized = {
        "name": str(payload.get("name", "")).strip(),
        "total_amount": round(float(payload.get("total_amount", 0)), 2),
        "monthly_emi": round(float(payload.get("monthly_emi", 0)), 2),
        "remaining_months": max(0, int(payload.get("remaining_months", 0))),
        "interest_rate": round(float(payload.get("interest_rate", 0) or 0), 2),
        "due_date": str(payload.get("due_date", "")).strip(),
        "source": "manual",
    }
    return Storage.add_emi(normalized)


def remove_emi(identifier: str) -> None:
    Storage.remove_emi(identifier)


def summarize_emis(transactions_df=None) -> dict:
    emis = get_all_emis(transactions_df)
    monthly_load = round(sum(float(item["monthly_emi"]) for item in emis), 2)
    remaining_liability = round(sum(float(item["monthly_emi"]) * max(int(item["remaining_months"]), 0) for item in emis), 2)
    return {
        "items": emis,
        "monthly_load": monthly_load,
        "remaining_liability": remaining_liability,
    }


def build_emi_alerts(transactions_df=None) -> list[dict]:
    today = date.today()
    alerts: list[dict] = []
    for emi in get_all_emis(transactions_df):
        due_date = _to_date(emi.get("due_date", ""))
        if due_date is None:
            continue
        delta = (due_date - today).days
        if delta < 0:
            alerts.append(
                {
                    "type": "emi_overdue",
                    "title": f"EMI Overdue: {emi['name']}",
                    "message": f"{emi['name']} monthly EMI of Rs. {round(float(emi['monthly_emi']), 2)} is overdue.",
                }
            )
        elif delta <= 5:
            alerts.append(
                {
                    "type": "emi_upcoming",
                    "title": f"Upcoming EMI: {emi['name']}",
                    "message": f"{emi['name']} EMI of Rs. {round(float(emi['monthly_emi']), 2)} is due in {delta} days.",
                }
            )
    return alerts
