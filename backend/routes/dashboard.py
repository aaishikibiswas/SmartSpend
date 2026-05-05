import asyncio
from fastapi import APIRouter
from pydantic import BaseModel

from backend.services.anomaly_engine import latest_anomaly_summary
from backend.services.advisory_engine import generate_financial_advice
from backend.services.analytics import get_dashboard_analytics
from backend.services.behavior_engine import build_behavior_profile
from backend.services.budget_engine import build_budget_snapshot
from backend.services.cashflow_engine import build_cashflow_timeline
from backend.services.emi_engine import summarize_emis
from backend.services.expense_classifier import classify_expense_split
from backend.models.predict import build_daily_expense_series, predict_next_expense
from backend.services.networth_engine import calculate_networth
from backend.services.priority_engine import build_priorities
from backend.services.subscription_engine import get_all_subscriptions
from backend.storage import Storage, bills_db

router = APIRouter()


def build_category_comparison(transactions):
    if transactions.empty:
        return []

    df = transactions.copy()
    expenses = df[df["amount"] < 0].copy()
    if expenses.empty:
        return []

    grouped = expenses.groupby("category")["amount"].sum().reset_index().sort_values("amount")

    return [
        {
            "name": row["category"],
            "amount": round(abs(float(row["amount"])), 2),
        }
        for _, row in grouped.iterrows()
    ]


def build_goal_suggestion(metrics: dict, budget_snapshot: dict) -> dict:
    leftover = max(0.0, float(budget_snapshot["global"]["remaining_amount"]))
    suggested = round(min(leftover * 0.45, max(float(metrics["netSavings"]) * 0.3, 0.0)), 2)
    return {
        "recommendedContribution": suggested,
        "message": f"Based on your remaining budget, consider moving Rs{round(suggested):,} toward your top savings goal." if suggested > 0 else "Hold contributions for now and stabilize monthly spending first.",
    }


@router.get("/")
async def get_dashboard():
    transactions = Storage.get_transactions()
    metrics = await get_dashboard_analytics()
    
    # Offload heavy sync tasks to threads
    budget_snapshot = await asyncio.to_thread(build_budget_snapshot, transactions)
    category_chart = await asyncio.to_thread(build_category_comparison, transactions)
    subscriptions = await asyncio.to_thread(get_all_subscriptions, transactions)
    emi_summary = await asyncio.to_thread(summarize_emis)
    expense_split = await asyncio.to_thread(classify_expense_split, transactions, subscriptions, emi_summary, bills_db)
    networth = await asyncio.to_thread(calculate_networth, metrics, emi_summary)
    cashflow = await asyncio.to_thread(build_cashflow_timeline, subscriptions, emi_summary, bills_db, transactions)
    
    daily_series = await asyncio.to_thread(build_daily_expense_series, transactions)
    prediction = await asyncio.to_thread(predict_next_expense, daily_series, include_prophet=False)
    
    anomaly = await asyncio.to_thread(latest_anomaly_summary, transactions)
    behavior = await asyncio.to_thread(build_behavior_profile, transactions)
    
    advisory = await generate_financial_advice(metrics, budget_snapshot, prediction, expense_split, behavior)
    priorities = await asyncio.to_thread(build_priorities, metrics, budget_snapshot, subscriptions, emi_summary, cashflow)
    sorted_transactions = transactions.sort_values("date", ascending=False)
    recent_transactions = sorted_transactions.head(5).to_dict(orient="records")
    all_transactions = sorted_transactions.to_dict(orient="records")

    return {
        "status": 200,
        "data": {
            "metrics": metrics,
            "budgeting": budget_snapshot,
            "goalSuggestion": build_goal_suggestion(metrics, budget_snapshot),
            "categoryBreakdown": category_chart,
            "subscriptions": subscriptions,
            "emi": emi_summary,
            "expenseSplit": expense_split,
            "networth": networth,
            "cashflow": cashflow,
            "priorities": priorities,
            "anomalySummary": anomaly,
            "behavior": behavior,
            "advisory": advisory,
            "prediction": prediction,
            "bills": bills_db,
            "recentTransactions": recent_transactions,
            "allTransactions": all_transactions,
        },
    }


class AdviceRequest(BaseModel):
    metrics: dict
    budgeting: dict
    prediction: dict
    expenseSplit: dict
    behavior: dict | None = None


@router.post("/smart-advice")
async def get_smart_advice(payload: AdviceRequest):
    """
    Direct endpoint for real-time Smart Advice generation.
    """
    advisory = await generate_financial_advice(
        payload.metrics, 
        payload.budgeting, 
        payload.prediction, 
        payload.expenseSplit, 
        payload.behavior
    )
    return {
        "status": 200,
        "data": advisory,
    }
