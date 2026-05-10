from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timedelta

import pandas as pd

from backend.storage import Storage


SUBSCRIPTION_KEYWORDS = (
    "autopay",
    "auto debit",
    "auto-debit",
    "standing instruction",
    "si debit",
    "nach",
    "recurring",
    "monthly",
    "netflix",
    "spotify",
    "prime",
    "amazon prime",
    "youtube",
    "youtube premium",
    "subscription",
    "membership",
    "icloud",
    "chatgpt",
    "hotstar",
    "apple music",
    "google one",
    "adobe",
    "gym",
    "canva",
    "notion",
    "microsoft",
    "disney",
    "zee5",
    "sony liv",
    "broadband",
    "recharge",
)
UTILITY_KEYWORDS = ("rent", "electricity", "water", "internet", "broadband", "wifi", "phone", "postpaid", "insurance")
EMI_KEYWORDS = ("emi", "loan", "finance", "mortgage", "installment", "instalment", "credit card emi", "education loan", "bike emi", "laptop emi", "phone emi")
CATEGORY_RECURRING_HINTS = {"Bills", "Utilities", "Subscription", "Rent", "Housing", "Telecom", "Insurance"}
CATEGORY_EMI_HINTS = {"Emi", "Loan", "Housing", "Finance"}


def _normalize_dates(values: list[str]) -> list[datetime]:
    dates: list[datetime] = []
    for value in values:
        try:
            dates.append(datetime.fromisoformat(str(value)))
        except ValueError:
            parsed = pd.to_datetime(value, errors="coerce")
            if pd.notna(parsed):
                dates.append(parsed.to_pydatetime())
    return sorted(dates)


def _detect_interval(day_gaps: list[int]) -> tuple[str, int] | None:
    if not day_gaps:
        return None
    avg_gap = sum(day_gaps) / len(day_gaps)
    if 5 <= avg_gap <= 9:
        return ("Weekly", 7)
    if 25 <= avg_gap <= 35:
        return ("Monthly", 30)
    if 80 <= avg_gap <= 100:
        return ("Quarterly", 91)
    if 350 <= avg_gap <= 380:
        return ("Yearly", 365)
    return None


def _monthly_multiplier(frequency: str) -> float:
    lookup = {
        "Weekly": 4.33,
        "Monthly": 1.0,
        "Quarterly": 1 / 3,
        "Yearly": 1 / 12,
    }
    return lookup.get(frequency, 1.0)


def _interval_from_label(label: str | None) -> tuple[str, int] | None:
    normalized = str(label or "").strip().lower()
    if normalized == "weekly":
        return ("Weekly", 7)
    if normalized == "monthly":
        return ("Monthly", 30)
    if normalized == "quarterly":
        return ("Quarterly", 91)
    if normalized == "yearly":
        return ("Yearly", 365)
    return None


def _safe_float(value, default: float = 0.0) -> float:
    try:
        if pd.isna(value):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _truthy(value) -> bool:
    if value is None:
        return False
    if isinstance(value, float) and pd.isna(value):
        return False
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y"}
    return bool(value)


def _latest_value(rows: list[dict], key: str, default=None):
    for row in reversed(rows):
        value = row.get(key)
        if value not in (None, ""):
            return value
    return default


def _text_blob(row: dict) -> str:
    parts = [
        row.get("merchant"),
        row.get("category"),
        row.get("narration"),
        row.get("description"),
        row.get("language"),
        row.get("payment_method"),
        row.get("source"),
        row.get("bank_source"),
        row.get("liability_type"),
    ]
    return " ".join(str(part) for part in parts if part not in (None, "")).strip().lower()


def _recurring_confidence(
    merchant_key: str,
    category: str,
    amount_stability: float,
    average_amount: float,
    interval_found: bool,
    source_confidence: float,
    row_count: int,
) -> float:
    score = 0.0
    if interval_found:
        score += 0.42
    if amount_stability <= max(average_amount * 0.12, 75):
        score += 0.22
    elif amount_stability <= max(average_amount * 0.2, 150):
        score += 0.12
    if any(keyword in merchant_key for keyword in (*SUBSCRIPTION_KEYWORDS, *UTILITY_KEYWORDS, *EMI_KEYWORDS)):
        score += 0.18
    if category in CATEGORY_RECURRING_HINTS or category in CATEGORY_EMI_HINTS:
        score += 0.1
    if row_count >= 3:
        score += 0.06
    score = max(score, source_confidence)
    return round(min(score, 0.98), 2)


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
                "reference": row.get("transaction_reference") or row.get("reference") or row.get("id"),
                "payment_method": row.get("payment_method") or row.get("method") or "",
                "source": row.get("bank_source") or row.get("source") or "",
                "bank_source": row.get("bank_source") or "",
                "narration": row.get("narration") or row.get("description") or row.get("language") or "",
                "description": row.get("description") or "",
                "mcc": row.get("mcc") or "",
                "recurring_confidence": _safe_float(row.get("recurring_confidence"), 0.0),
                "is_subscription": _truthy(row.get("is_subscription")) or _truthy(row.get("subscription_detection")),
                "is_emi": _truthy(row.get("is_emi")) or _truthy(row.get("emi_detection")),
                "subscription": row.get("subscription_detection") or {},
                "emi": row.get("emi_detection") or {},
                "installment": row.get("installment") or row.get("installment_metadata") or {},
                "liability_type": row.get("liability_type") or "",
            }
        )
    return grouped


def _detected_recurring_rows(transactions_df: pd.DataFrame) -> list[dict]:
    if transactions_df.empty:
        return []

    detected: list[dict] = []
    for merchant, rows in _group_recurring_candidates(transactions_df).items():
        merchant_key = merchant.strip().lower()
        rows = sorted(rows, key=lambda item: item["date"])
        text_key = " ".join(_text_blob(row) for row in rows)
        dates = _normalize_dates([row["date"] for row in rows])
        if not dates:
            continue

        gaps = [(dates[index] - dates[index - 1]).days for index in range(1, len(dates))]
        interval = _detect_interval(gaps)
        metadata_interval = None
        latest_subscription = _latest_value(rows, "subscription", {}) or {}
        if isinstance(latest_subscription, dict):
            metadata_interval = _interval_from_label(latest_subscription.get("interval"))
        latest_liability_type = str(_latest_value(rows, "liability_type", "") or "").strip().lower()
        if not interval and (any(row.get("is_emi") for row in rows) or latest_liability_type in {"bill", "rent"}):
            metadata_interval = ("Monthly", 30)
        if not interval:
            interval = metadata_interval
        source_confidence = max((_safe_float(row.get("recurring_confidence"), 0.0) for row in rows), default=0.0)
        if not interval or (len(rows) < 2 and source_confidence < 0.7):
            continue

        recent_rows = rows[-3:]
        average_amount = sum(item["amount"] for item in recent_rows) / len(recent_rows)
        amount_stability = max(item["amount"] for item in recent_rows) - min(item["amount"] for item in recent_rows)
        latest_category = str(rows[-1]["category"]).title()
        confidence = _recurring_confidence(
            text_key,
            latest_category,
            amount_stability,
            average_amount,
            interval_found=bool(gaps),
            source_confidence=source_confidence,
            row_count=len(rows),
        )
        if confidence < 0.5:
            continue

        frequency, interval_days = interval
        latest_amount = float(rows[-1]["amount"])
        monthly_cost = round(average_amount * _monthly_multiplier(frequency), 2)
        last_charge = dates[-1]
        is_emi = (
            any(keyword in text_key for keyword in EMI_KEYWORDS)
            or latest_category in CATEGORY_EMI_HINTS
            or any(row.get("is_emi") for row in rows)
        )
        is_subscription = (
            any(keyword in text_key for keyword in SUBSCRIPTION_KEYWORDS)
            or latest_category in {"Subscription", "Entertainment", "Telecom"}
            or any(row.get("is_subscription") for row in rows)
        )
        is_utility = any(keyword in text_key for keyword in UTILITY_KEYWORDS) or latest_category in CATEGORY_RECURRING_HINTS

        if not (is_emi or is_subscription or is_utility or amount_stability <= max(average_amount * 0.15, 100)):
            continue

        payment_type = "EMI" if is_emi else ("Subscription" if is_subscription else "Recurring Bill")
        detected.append(
            {
                "name": merchant,
                "frequency": frequency,
                "interval_days": interval_days,
                "monthly_cost": monthly_cost,
                "yearly_cost": round(monthly_cost * 12, 2),
                "last_charge_date": last_charge.date().isoformat(),
                "next_due_date": (last_charge + timedelta(days=interval_days)).date().isoformat(),
                "due_date": (last_charge + timedelta(days=interval_days)).date().isoformat(),
                "latest_amount": round(latest_amount, 2),
                "average_amount": round(average_amount, 2),
                "payment_type": payment_type,
                "status": "active",
                "recurring_confidence": confidence,
                "category": latest_category,
                "mcc": _latest_value(rows, "mcc", ""),
                "payment_method": _latest_value(rows, "payment_method", ""),
                "transaction_reference": _latest_value(rows, "reference", ""),
                "source": _latest_value(rows, "source", "auto"),
                "installment_metadata": _latest_value(rows, "installment", {}) or {},
                "liability_type": _latest_value(rows, "liability_type", "EMI" if is_emi else ""),
                "history": rows,
                "history_count": len(rows),
            }
        )

    return detected


def detect_subscriptions(transactions_df: pd.DataFrame) -> list[dict]:
    if transactions_df.empty:
        return []

    suppressed = Storage.get_suppressed_subscriptions()
    subscriptions: list[dict] = []

    for item in _detected_recurring_rows(transactions_df):
        merchant_key = str(item.get("name", "")).strip().lower()
        if merchant_key in suppressed:
            continue
        if item.get("payment_type") == "EMI":
            continue

        subscriptions.append(
            {
                key: value
                for key, value in item.items()
                if key != "history"
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
        "payment_type": "Subscription",
        "status": "active",
        "recurring_confidence": round(float(payload.get("recurring_confidence", 1.0)), 2),
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

    for item in _detected_recurring_rows(transactions_df):
        merchant_key = str(item.get("name", "")).strip().lower()
        if merchant_key in suppressed:
            continue
        if item.get("payment_type") != "EMI" or item.get("frequency") != "Monthly":
            continue

        monthly_emi = round(float(item["monthly_cost"]), 2)
        installment = item.get("installment_metadata") or {}
        emis.append(
            {
                "id": f"auto-{merchant_key.replace(' ', '-')}",
                "name": item["name"],
                "total_amount": round(float(installment.get("total_amount", monthly_emi * 12)) if isinstance(installment, dict) else monthly_emi * 12, 2),
                "monthly_emi": monthly_emi,
                "remaining_months": int(installment.get("remaining_months", 12)) if isinstance(installment, dict) else 12,
                "interest_rate": round(float(installment.get("interest_rate", 0.0)), 2) if isinstance(installment, dict) else 0.0,
                "due_date": item["next_due_date"],
                "payment_type": "EMI",
                "status": "active",
                "recurring_confidence": item.get("recurring_confidence", 0.0),
                "transaction_reference": item.get("transaction_reference", ""),
                "payment_method": item.get("payment_method", ""),
                "liability_type": item.get("liability_type", "EMI"),
                "source": "auto",
            }
        )

    emis.sort(key=lambda item: item["monthly_emi"], reverse=True)
    return emis


def detect_recurring_increases(transactions_df: pd.DataFrame) -> list[dict]:
    alerts: list[dict] = []
    if transactions_df.empty:
        return alerts

    for item in _detected_recurring_rows(transactions_df):
        history = item.get("history", [])
        if len(history) < 3:
            continue
        previous = [float(row["amount"]) for row in history[:-1][-4:]]
        latest = float(history[-1]["amount"])
        baseline = sum(previous) / len(previous) if previous else 0
        if baseline <= 0:
            continue
        increase_pct = ((latest - baseline) / baseline) * 100
        if increase_pct >= 15 and (latest - baseline) >= 75:
            alerts.append(
                {
                    "type": "recurring_increase",
                    "title": f"{item['payment_type']} Increased: {item['name']}",
                    "message": f"{item['name']} rose {round(increase_pct)}% to Rs. {round(latest, 2)} from its usual Rs. {round(baseline, 2)} pattern.",
                }
            )
    return alerts[:4]


def detect_recurring_candidates(transactions_df: pd.DataFrame) -> list[dict]:
    return [
        {key: value for key, value in item.items() if key != "history"}
        for item in _detected_recurring_rows(transactions_df)
    ]
