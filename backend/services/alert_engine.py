from __future__ import annotations

from backend.services.anomaly_engine import score_transaction_anomalies
from backend.services.budget_engine import get_budget_snapshot
from backend.services.emi_engine import build_emi_alerts, summarize_emis
from backend.services.expense_classifier import classify_expense_split
from backend.services.subscription_engine import get_all_subscriptions
from backend.storage import Storage
from backend.storage import bills_db


def generate_alerts(df):
    if df.empty:
        return

    expenses = df[df["amount"] < 0].copy()
    expenses["amount"] = expenses["amount"].abs()

    if not expenses.empty:
        mean_expense = expenses["amount"].mean()
        std_expense = expenses["amount"].std() if len(expenses) > 1 else 0
        high_t_threshold = mean_expense + (2 * std_expense)

        high_txs = expenses[expenses["amount"] > high_t_threshold]
        for _, tx in high_txs.iterrows():
            Storage.add_alert(
                {
                    "type": "high_transaction",
                    "title": "High Transaction Alert",
                    "message": f"{tx['merchant']} purchase of Rs. {round(float(tx['amount']), 2)} is unusually high based on your history.",
                }
            )

        dupes = expenses.duplicated(subset=["date", "merchant", "amount"], keep=False)
        if dupes.any():
            dupe_rows = expenses[dupes]
            merchant = dupe_rows.iloc[0]["merchant"]
            amt = round(float(dupe_rows.iloc[0]["amount"]), 2)
            Storage.add_alert(
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
        Storage.add_alert(
            {
                "type": "global_breach",
                "title": "Monthly Budget Exceeded",
                "message": f"You have exceeded your monthly budget by Rs. {round(abs(global_budget['remaining_amount']), 2)}.",
            }
        )
    elif global_budget["usage_percent"] >= 80:
        Storage.add_alert(
            {
                "type": "global_warning",
                "title": "Global Budget Warning",
                "message": f"You have already used {round(global_budget['usage_percent'])}% of your monthly budget.",
            }
        )

    for category in category_budgets:
        if category["usage_percent"] >= 100:
            Storage.add_alert(
                {
                    "type": "breach",
                    "title": f"Budget Breached: {category['name']}",
                    "message": f"You overspent {category['name']} by Rs. {round(abs(category['remaining_amount']), 2)}.",
                }
            )
        elif category["usage_percent"] >= 80:
            Storage.add_alert(
                {
                    "type": "warning",
                    "title": f"Budget Warning: {category['name']}",
                    "message": f"{category['name']} is already at {round(category['usage_percent'])}% of budget.",
                }
            )

    for alert in build_emi_alerts():
        Storage.add_alert(alert)

    expense_split = classify_expense_split(df, get_all_subscriptions(df), summarize_emis(df), bills_db)
    if expense_split["fixed_percent"] > 70:
        Storage.add_alert(
            {
                "type": "fixed_ratio",
                "title": "High Fixed Expense Ratio",
                "message": f"Fixed commitments are {round(float(expense_split['fixed_percent']))}% of your outflow. Reduce locked-in costs where possible.",
            }
        )
    if expense_split["variable_percent"] > 60:
        Storage.add_alert(
            {
                "type": "variable_spend",
                "title": "Excess Variable Spending",
                "message": f"Variable expenses are at {round(float(expense_split['variable_percent']))}% of your outflow. Review flexible spending categories.",
            }
        )

    for anomaly in score_transaction_anomalies(df)[:3]:
        Storage.add_alert(
            {
                "type": "anomaly",
                "title": f"Anomalous Transaction: {anomaly['merchant']}",
                "message": f"{anomaly['merchant']} on {anomaly['date']} for Rs. {anomaly['amount']} was flagged with {anomaly['risk_flag']} anomaly risk.",
            }
        )


def get_all_alerts():
    from backend.storage import alerts_db

    return alerts_db
