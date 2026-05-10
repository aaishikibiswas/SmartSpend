from __future__ import annotations

from datetime import datetime

import pandas as pd

from backend.services.anomaly_engine import score_transaction_anomalies
from backend.services.budget_engine import get_budget_snapshot
from backend.services.emi_engine import build_emi_alerts, summarize_emis
from backend.services.expense_classifier import classify_expense_split
from backend.services.subscription_engine import detect_recurring_candidates, detect_recurring_increases, get_all_subscriptions
from backend.storage import Storage


def _money(value: float) -> str:
    return f"Rs. {round(float(value), 2)}"


def _dated_frame(df):
    dated = df.copy()
    dated["parsed_date"] = pd.to_datetime(dated["date"], errors="coerce")
    return dated.dropna(subset=["parsed_date"])


def _income_expense_totals(df) -> tuple[float, float]:
    income = round(float(df[df["amount"] > 0]["amount"].sum()), 2) if not df.empty else 0.0
    expense = round(abs(float(df[df["amount"] < 0]["amount"].sum())), 2) if not df.empty else 0.0
    return income, expense


def _build_pressure_alerts(df, budget_snapshot: dict, subscriptions: list[dict], emi_summary: dict, expense_split: dict) -> list[dict]:
    alerts: list[dict] = []
    income, expense = _income_expense_totals(df)
    subscription_load = sum(float(item.get("monthly_cost", 0)) for item in subscriptions)
    emi_load = float(emi_summary.get("monthly_load", 0))
    fixed_load = float(expense_split.get("fixed_total", 0))
    recurring_load = subscription_load + emi_load

    if income > 0:
        emi_ratio = (emi_load / income) * 100
        if emi_ratio >= 40:
            alerts.append(
                {
                    "type": "emi_pressure",
                    "title": "High EMI Pressure",
                    "message": f"EMIs are consuming {round(emi_ratio)}% of monthly income. Keep liquidity ready before discretionary spend.",
                }
            )

        projected_outflow = expense + recurring_load
        if projected_outflow > income:
            alerts.append(
                {
                    "type": "negative_cashflow",
                    "title": "Negative Cash Flow Risk",
                    "message": f"Projected monthly outflow is {_money(projected_outflow - income)} above income after recurring commitments.",
                }
            )

        fixed_ratio = (fixed_load / income) * 100
        if fixed_ratio >= 65:
            alerts.append(
                {
                    "type": "fixed_commitment_pressure",
                    "title": "Fixed Commitment Pressure",
                    "message": f"Fixed commitments are {round(fixed_ratio)}% of income, leaving limited room for variable expenses.",
                }
            )

    burn_rate = expense / max(datetime.now().day, 1)
    remaining = float(budget_snapshot["global"].get("remaining_amount", 0))
    runway_days = remaining / max(burn_rate, 1)
    if remaining > 0 and runway_days < 7:
        alerts.append(
            {
                "type": "low_runway",
                "title": "Low Runway Risk",
                "message": f"At the current burn rate, remaining monthly budget may last only {round(runway_days, 1)} days.",
            }
        )

    return alerts


def _build_spending_streak_alerts(df) -> list[dict]:
    dated = _dated_frame(df)
    expenses = dated[dated["amount"] < 0].copy()
    if len(expenses) < 6:
        return []

    expenses["spend"] = expenses["amount"].abs()
    daily = expenses.groupby(expenses["parsed_date"].dt.date)["spend"].sum().sort_index()
    if len(daily) < 6:
        return []

    recent = daily.tail(3)
    baseline = daily.iloc[:-3].tail(14)
    if baseline.empty:
        return []
    threshold = max(float(baseline.mean()) * 1.35, float(baseline.mean()) + 500)
    if len(recent) == 3 and all(value > threshold for value in recent):
        return [
            {
                "type": "overspending_streak",
                "title": "Overspending Streak Detected",
                "message": f"Daily spending has stayed above your normal range for 3 straight active days.",
            }
        ]
    return []


def _build_balance_drop_alerts(df) -> list[dict]:
    dated = _dated_frame(df)
    if len(dated) < 4:
        return []

    recent = dated.sort_values("parsed_date").tail(5)
    net_recent = round(float(recent["amount"].sum()), 2)
    income, _ = _income_expense_totals(dated)
    threshold = max(income * 0.2, 5000)
    if net_recent < -threshold:
        return [
            {
                "type": "balance_drop",
                "title": "Sudden Balance Drop",
                "message": f"Recent account activity reduced balance by {_money(abs(net_recent))}. Review the latest debits.",
            }
        ]
    return []


def _build_recurring_discovery_alerts(df, recurring_candidates: list[dict], income: float) -> list[dict]:
    alerts: list[dict] = []
    for item in recurring_candidates[:8]:
        history_count = int(item.get("history_count", 0) or 0)
        confidence = float(item.get("recurring_confidence", 0) or 0)
        payment_type = str(item.get("payment_type", "Recurring Payment"))
        monthly_cost = float(item.get("monthly_cost", 0) or 0)
        name = item.get("name", "Recurring payment")
        if history_count <= 1 and confidence >= 0.7:
            if payment_type == "EMI":
                alerts.append(
                    {
                        "type": "new_emi_detected",
                        "title": f"New EMI Detected: {name}",
                        "message": f"{name} was identified as an EMI liability with an estimated monthly load of {_money(monthly_cost)}.",
                    }
                )
            else:
                alerts.append(
                    {
                        "type": "new_subscription_detected",
                        "title": f"New recurring subscription detected: {name}",
                        "message": f"{name} looks like a {payment_type.lower()} with {round(confidence * 100)}% recurring confidence.",
                    }
                )

    seen_today: set[str] = set()
    dated = _dated_frame(df)
    expenses = dated[dated["amount"] < 0].copy()
    if not expenses.empty:
        expenses["amount_abs"] = expenses["amount"].abs().round(2)
        expenses["tx_day"] = expenses["parsed_date"].dt.date
        duplicate_rows = expenses[expenses.duplicated(subset=["merchant", "amount_abs", "tx_day"], keep=False)]
        for _, row in duplicate_rows.head(3).iterrows():
            key = f"{row['merchant']}::{row['amount_abs']}"
            if key in seen_today:
                continue
            seen_today.add(key)
            alerts.append(
                {
                    "type": "duplicate_recurring_debit",
                    "title": "Potential duplicate subscription found",
                    "message": f"{row['merchant']} has repeated debits of {_money(float(row['amount_abs']))} on the same day.",
                }
            )

    recurring_load = sum(float(item.get("monthly_cost", 0) or 0) for item in recurring_candidates)
    if income > 0 and recurring_load / income >= 0.35:
        alerts.append(
            {
                "type": "liability_burden",
                "title": "Recurring liabilities may impact savings goals",
                "message": f"Detected recurring commitments are using {round((recurring_load / income) * 100)}% of monthly income.",
            }
        )
    return alerts


def generate_alerts(df):
    alerts = []
    if df.empty:
        return alerts

    expenses = df[df["amount"] < 0].copy()
    expenses["amount"] = expenses["amount"].abs()

    if not expenses.empty:
        mean_expense = expenses["amount"].mean()
        std_expense = expenses["amount"].std() if len(expenses) > 1 else 0
        high_t_threshold = mean_expense + (2 * std_expense)

        high_txs = expenses[expenses["amount"] > high_t_threshold].sort_values("date", ascending=False).head(5)
        for _, tx in high_txs.iterrows():
            alerts.append(
                {
                    "type": "high_transaction",
                    "title": "High Transaction Alert",
                    "message": f"{tx['merchant']} purchase of Rs. {round(float(tx['amount']), 2)} on {tx['date']} is unusually high based on your history.",
                }
            )

        dupes = expenses.duplicated(subset=["date", "merchant", "amount"], keep=False)
        if dupes.any():
            dupe_rows = expenses[dupes]
            merchant = dupe_rows.iloc[0]["merchant"]
            amt = round(float(dupe_rows.iloc[0]["amount"]), 2)
            alerts.append(
                {
                    "type": "duplicate",
                    "title": "Duplicate Detection",
                    "message": f"Identified multiple Rs. {amt} charges at {merchant} on {dupe_rows.iloc[0]['date']}.",
                }
            )

    budget_snapshot = get_budget_snapshot(df)
    global_budget = budget_snapshot["global"]
    category_budgets = budget_snapshot["categories"]

    if global_budget["usage_percent"] >= 100:
        alerts.append(
            {
                "type": "global_breach",
                "title": "Monthly Budget Exceeded",
                "message": f"You have exceeded your monthly budget by Rs. {round(abs(global_budget['remaining_amount']), 2)}.",
            }
        )
    elif global_budget["usage_percent"] >= 80:
        alerts.append(
            {
                "type": "global_warning",
                "title": "Global Budget Warning",
                "message": f"You have already used {round(global_budget['usage_percent'])}% of your monthly budget.",
            }
        )

    for category in category_budgets:
        if category["usage_percent"] >= 100:
            alerts.append(
                {
                    "type": "breach",
                    "title": f"Budget Breached: {category['name']}",
                    "message": f"You overspent {category['name']} by Rs. {round(abs(category['remaining_amount']), 2)}.",
                }
            )
        elif category["usage_percent"] >= 80:
            alerts.append(
                {
                    "type": "warning",
                    "title": f"Budget Warning: {category['name']}",
                    "message": f"{category['name']} is already at {round(category['usage_percent'])}% of budget.",
                }
            )

    subscriptions = get_all_subscriptions(df)
    emi_summary = summarize_emis(df)
    recurring_candidates = detect_recurring_candidates(df)
    income, _expense = _income_expense_totals(df)

    for alert in build_emi_alerts(df):
        alerts.append(alert)

    expense_split = classify_expense_split(df, subscriptions, emi_summary, Storage.get_bills())
    if expense_split["fixed_percent"] > 70:
        alerts.append(
            {
                "type": "fixed_ratio",
                "title": "High Fixed Expense Ratio",
                "message": f"Fixed commitments are {round(float(expense_split['fixed_percent']))}% of your outflow. Reduce locked-in costs where possible.",
            }
        )
    if expense_split["variable_percent"] > 60:
        alerts.append(
            {
                "type": "variable_spend",
                "title": "Excess Variable Spending",
                "message": f"Variable expenses are at {round(float(expense_split['variable_percent']))}% of your outflow. Review flexible spending categories.",
            }
        )

    alerts.extend(detect_recurring_increases(df))
    alerts.extend(_build_recurring_discovery_alerts(df, recurring_candidates, income))
    alerts.extend(_build_pressure_alerts(df, budget_snapshot, subscriptions, emi_summary, expense_split))
    alerts.extend(_build_spending_streak_alerts(df))
    alerts.extend(_build_balance_drop_alerts(df))

    for anomaly in score_transaction_anomalies(df)[:3]:
        anomaly_type = "recurring_anomaly" if anomaly.get("reason") == "recurring/liability pattern" else "anomaly"
        alerts.append(
            {
                "type": anomaly_type,
                "title": f"Anomalous Transaction: {anomaly['merchant']}",
                "message": f"{anomaly['merchant']} on {anomaly['date']} for Rs. {anomaly['amount']} was flagged with {anomaly['risk_flag']} anomaly risk from {anomaly.get('reason', 'spend behavior')}.",
            }
        )

    deduped: list[dict] = []
    seen: set[str] = set()
    for alert in alerts:
        key = f"{alert.get('title')}::{alert.get('message')}"
        if key in seen:
            continue
        seen.add(key)
        deduped.append(alert)

    return deduped


def get_all_alerts():
    from backend.storage import Storage

    return Storage.get_alerts()
