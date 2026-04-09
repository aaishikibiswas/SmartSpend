from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta

import pandas as pd

from backend.storage import Storage


SUBSCRIPTION_KEYWORDS = ("netflix", "spotify", "prime", "youtube", "subscription", "membership", "icloud", "chatgpt", "hotstar")
EMI_KEYWORDS = ("emi", "loan", "finance", "mortgage", "installment")


def _normalize_dates(values: list[str]) -> list[datetime]:
    dates: list[datetime] = []
    for value in values:
        try:
            dates.append(datetime.fromisoformat(str(value)))
        except ValueError:
            continue
    return sorted(dates)


def _detect_interval(day_gaps: list[int]) -> tuple[str, int] | None:
    if not day_gaps:
        return None
    avg_gap = sum(day_gaps) / len(day_gaps)
    if 5 <= avg_gap <= 9:
        return ("Weekly", 7)
    if 25 <= avg_gap <= 35:
        return ("Monthly", 30)
    return None


def _group_recurring_candidates(transactions_df: pd.DataFrame) -> dict[str, list[dict]]:
    expenses = transactions_df[transactions_df["amount"] < 0].copy()
    grouped: dict[str, list[dict]] = defaultdict(list)
    for _, row in expenses.iterrows():
        merchant = str(row.get("merchant", "")).strip()
        if not merchant:
            continue
        grouped[merchant].append(
            {
                "date": str(row.get("date", "")),
                "amount": abs(float(row.get("amount", 0))),
                "category": str(row.get("category", "Other")).title(),
            }
        )
    return grouped


def detect_subscriptions(transactions_df: pd.DataFrame) -> list[dict]:
    if transactions_df.empty:
        return []

    suppressed = Storage.get_suppressed_subscriptions()
    subscriptions: list[dict] = []

    for merchant, rows in _group_recurring_candidates(transactions_df).items():
        merchant_key = merchant.strip().lower()
        if merchant_key in suppressed or len(rows) < 2:
            continue

        rows = sorted(rows, key=lambda item: item["date"])
        dates = _normalize_dates([row["date"] for row in rows])
        if len(dates) < 2:
            continue

        gaps = [(dates[index] - dates[index - 1]).days for index in range(1, len(dates))]
        interval = _detect_interval(gaps)
        if not interval:
            continue

        average_amount = sum(item["amount"] for item in rows[-3:]) / min(3, len(rows))
        amount_stability = max(item["amount"] for item in rows[-3:]) - min(item["amount"] for item in rows[-3:])
        looks_like_subscription = (
            any(keyword in merchant_key for keyword in SUBSCRIPTION_KEYWORDS)
            or rows[-1]["category"] in {"Bills", "Utilities", "Subscription"}
            or amount_stability <= max(average_amount * 0.15, 100)
        )
        if not looks_like_subscription or any(keyword in merchant_key for keyword in EMI_KEYWORDS) or rows[-1]["category"] in {"Emi", "Loan", "Housing"}:
            continue

        frequency, interval_days = interval
        monthly_cost = round(average_amount * (4.33 if frequency == "Weekly" else 1), 2)
        last_charge = dates[-1]
        subscriptions.append(
            {
                "name": merchant,
                "frequency": frequency,
                "monthly_cost": monthly_cost,
                "yearly_cost": round(monthly_cost * 12, 2),
                "last_charge_date": last_charge.date().isoformat(),
                "next_due_date": (last_charge + timedelta(days=interval_days)).date().isoformat(),
            }
        )

    subscriptions.sort(key=lambda item: item["monthly_cost"], reverse=True)
    return subscriptions


def get_manual_subscriptions() -> list[dict]:
    return [{**item, "source": item.get("source", "manual")} for item in Storage.get_subscriptions()]


def get_all_subscriptions(transactions_df: pd.DataFrame | None = None) -> list[dict]:
    detected = [{**item, "source": "auto"} for item in detect_subscriptions(transactions_df if transactions_df is not None else Storage.get_transactions())]
    manual = get_manual_subscriptions()
    combined: list[dict] = []
    seen: set[str] = set()

    for item in [*manual, *detected]:
        key = str(item.get("name", "")).strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        combined.append(item)

    combined.sort(key=lambda item: float(item.get("monthly_cost", 0)), reverse=True)
    return combined


def add_subscription(payload: dict) -> dict:
    normalized = {
        "name": str(payload.get("name", "")).strip(),
        "frequency": str(payload.get("frequency", "Monthly")).strip() or "Monthly",
        "monthly_cost": round(float(payload.get("monthly_cost", 0)), 2),
        "yearly_cost": round(float(payload.get("monthly_cost", 0)) * 12, 2),
        "last_charge_date": str(payload.get("last_charge_date", "")).strip(),
        "next_due_date": str(payload.get("next_due_date", "")).strip(),
        "source": "manual",
    }
    return Storage.add_subscription(normalized)


def remove_subscription(name: str) -> None:
    removed_manual = Storage.remove_subscription(name)
    if not removed_manual:
        Storage.suppress_subscription(name)


def detect_emi_transactions(transactions_df: pd.DataFrame) -> list[dict]:
    if transactions_df.empty:
        return []

    suppressed = Storage.get_suppressed_emis()
    emis: list[dict] = []

    for merchant, rows in _group_recurring_candidates(transactions_df).items():
        merchant_key = merchant.strip().lower()
        if merchant_key in suppressed or len(rows) < 2:
            continue

        dates = _normalize_dates([row["date"] for row in rows])
        if len(dates) < 2:
            continue

        gaps = [(dates[index] - dates[index - 1]).days for index in range(1, len(dates))]
        interval = _detect_interval(gaps)
        if not interval or interval[0] != "Monthly":
            continue

        latest_category = rows[-1]["category"]
        if not (any(keyword in merchant_key for keyword in EMI_KEYWORDS) or latest_category in {"Emi", "Loan", "Housing"}):
            continue

        monthly_emi = round(sum(item["amount"] for item in rows[-3:]) / min(3, len(rows)), 2)
        last_charge = dates[-1]
        emis.append(
            {
                "id": f"auto-{merchant_key.replace(' ', '-')}",
                "name": merchant,
                "total_amount": round(monthly_emi * 12, 2),
                "monthly_emi": monthly_emi,
                "remaining_months": 12,
                "interest_rate": 0.0,
                "due_date": (last_charge + timedelta(days=30)).date().isoformat(),
                "source": "auto",
            }
        )

    emis.sort(key=lambda item: item["monthly_emi"], reverse=True)
    return emis
