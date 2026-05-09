from __future__ import annotations

import asyncio
import threading

import pandas as pd

from backend.models.predict import build_daily_expense_series, predict_next_expense
from backend.models.train import train_regression_model
from backend.services.alert_engine import generate_alerts, get_all_alerts
from backend.services.anomaly_engine import latest_anomaly_summary
from backend.services.analytics import get_dashboard_analytics
from backend.services.advisory_engine import generate_financial_advice
from backend.services.behavior_engine import build_behavior_profile
from backend.services.budget_engine import build_budget_snapshot, sync_budget_with_transactions
from backend.services.cashflow_engine import build_cashflow_timeline
from backend.services.emi_engine import summarize_emis
from backend.services.expense_classifier import classify_expense_split
from backend.services.goal_engine import get_all_goals
from backend.services.networth_engine import calculate_networth
from backend.services.priority_engine import build_priorities
from backend.services.subscription_engine import get_all_subscriptions
from backend.services.websocket_manager import websocket_manager
from backend.storage import Storage, bills_db


def _build_category_comparison(transactions: pd.DataFrame) -> list[dict]:
    if transactions.empty:
        return []

    expenses = transactions[transactions["amount"] < 0].copy()
    if expenses.empty:
        return []

    grouped = expenses.groupby("category")["amount"].sum().reset_index().sort_values("amount")
    return [
        {"name": row["category"], "amount": round(abs(float(row["amount"])), 2)}
        for _, row in grouped.iterrows()
    ]


def _build_goal_suggestion(metrics: dict, budget_snapshot: dict) -> dict:
    leftover = max(0.0, float(budget_snapshot["global"]["remaining_amount"]))
    suggested = round(min(leftover * 0.45, max(float(metrics["netSavings"]) * 0.3, 0.0)), 2)
    return {
        "recommendedContribution": suggested,
        "message": f"Based on your remaining budget, consider moving Rs{round(suggested):,} toward your top savings goal." if suggested > 0 else "Hold contributions for now and stabilize monthly spending first.",
    }


def _refresh_financial_state(transactions_df: pd.DataFrame) -> list[dict]:
    sync_budget_with_transactions(transactions_df)
    alerts = generate_alerts(transactions_df)
    new_alerts = Storage.sync_alerts(alerts)

    # Keep the request path fast and train in the background after core state updates.
    threading.Thread(target=train_regression_model, args=(transactions_df.copy(),), daemon=True).start()
    return new_alerts or []


async def _broadcast_post_refresh(snapshot: dict, source: str, transactions: list[dict] | None = None, new_alerts: list[dict] | None = None) -> None:
    if transactions:
        for transaction in transactions:
            await websocket_manager.broadcast(
                {
                    "type": "new_transaction",
                    "data": {
                        "source": source,
                        "transaction": transaction,
                    },
                }
            )

    if new_alerts and len(new_alerts) > 0:
        # Sort new alerts by ID descending, though they should already be in order of insertion.
        # But wait, snapshot["data"]["alerts"] is sorted and has all alerts.
        # We can just broadcast the full alerts array but set latest to the first new_alert.
        # Actually, new_alerts might not be sorted by ID descending here, let's just use the first new_alert
        # or the first alert from snapshot that is also in new_alerts.
        latest_new_alert = new_alerts[0] # the first inserted one is the most recent (highest ID)
        await websocket_manager.broadcast(
            {
                "type": "alert_trigger",
                "data": {
                    "source": source,
                    "alerts": snapshot["data"]["alerts"],
                    "latest": latest_new_alert,
                },
            }
        )

    await websocket_manager.broadcast(
        {
            "type": "prediction_update",
            "data": {
                "source": source,
                "prediction": snapshot["data"]["prediction"],
            },
        }
    )

    await websocket_manager.broadcast(snapshot)


async def _complete_uploaded_refresh(transactions: list[dict]) -> None:
    current_df = Storage.get_transactions()
    new_alerts = _refresh_financial_state(current_df)
    snapshot = await _build_snapshot(latest_transaction=transactions[-1] if transactions else None, event_type="update", source="upload")
    await _broadcast_post_refresh(snapshot, "upload", transactions, new_alerts)


async def _complete_live_refresh(transaction: dict) -> None:
    current_df = Storage.get_transactions()
    new_alerts = _refresh_financial_state(current_df)
    snapshot = await _build_snapshot(latest_transaction=transaction, event_type="update", source="stream")
    await _broadcast_post_refresh(snapshot, "stream", new_alerts=new_alerts)


async def _build_snapshot(latest_transaction: dict | None = None, event_type: str = "update", source: str = "system") -> dict:
    transactions = Storage.get_transactions()
    metrics = await get_dashboard_analytics()
    budgeting = build_budget_snapshot(transactions)
    subscriptions = get_all_subscriptions(transactions)
    emi_summary = summarize_emis()
    expense_split = classify_expense_split(transactions, subscriptions, emi_summary, bills_db)
    networth = calculate_networth(metrics, emi_summary)
    cashflow = build_cashflow_timeline(subscriptions, emi_summary, bills_db)
    prediction = {
        "forecast": {"peakAlert": {"day": "Refreshing...", "amount": 0}, "series": []},
        "next_expense_prediction": predict_next_expense(build_daily_expense_series(transactions), include_prophet=False),
    }
    anomaly = latest_anomaly_summary(transactions)
    behavior = build_behavior_profile(transactions)
    advisory = await generate_financial_advice(metrics, {"global": budgeting["global"]}, prediction["next_expense_prediction"], expense_split, behavior)
    recent_transactions = transactions.sort_values("date", ascending=False).head(5).to_dict(orient="records") if not transactions.empty else []

    return {
        "type": event_type,
        "data": {
            "source": source,
            "transaction": latest_transaction,
            "metrics": metrics,
            "budgeting": budgeting,
            "alerts": get_all_alerts(),
            "prediction": prediction,
            "goals": get_all_goals(),
            "goalSuggestion": _build_goal_suggestion(metrics, budgeting),
            "bills": bills_db,
            "subscriptions": subscriptions,
            "emi": emi_summary,
            "expenseSplit": expense_split,
            "expense_split": expense_split,
            "networth": networth,
            "cashflow": cashflow,
            "priorities": build_priorities(metrics, budgeting, subscriptions, emi_summary, cashflow),
            "anomalySummary": anomaly,
            "behavior": behavior,
            "advisory": advisory,
            "categoryBreakdown": _build_category_comparison(transactions),
            "recentTransactions": recent_transactions,
            "allTransactions": transactions.sort_values("date", ascending=False).to_dict(orient="records") if not transactions.empty else [],
        },
    }


async def broadcast_snapshot(latest_transaction: dict | None = None, event_type: str = "update", source: str = "system") -> None:
    await websocket_manager.broadcast(await _build_snapshot(latest_transaction=latest_transaction, event_type=event_type, source=source))


async def process_uploaded_transactions(transactions: list[dict]) -> None:
    Storage.replace_transactions(transactions)
    current_df = Storage.get_transactions()
    sync_budget_with_transactions(current_df)
    asyncio.create_task(_complete_uploaded_refresh(transactions))


async def process_live_transaction(transaction: dict) -> None:
    Storage.add_transaction(transaction)
    current_df = Storage.get_transactions()
    sync_budget_with_transactions(current_df)

    await websocket_manager.broadcast(
        {
            "type": "new_transaction",
            "data": {
                "source": "stream",
                "transaction": transaction,
            },
        }
    )
    asyncio.create_task(_complete_live_refresh(transaction))


async def get_current_snapshot() -> dict:
    return await _build_snapshot(event_type="snapshot", source="initial")
