import asyncio
from datetime import datetime

import pandas as pd
from fastapi import APIRouter
from pydantic import BaseModel

from backend.services.anomaly_engine import latest_anomaly_summary
from backend.services.advisory_engine import generate_financial_advice
from backend.services.behavior_engine import build_behavior_profile
from backend.services.budget_engine import build_budget_snapshot
from backend.services.cashflow_engine import build_cashflow_timeline
from backend.services.credit_score_engine import calculate_credit_score
from backend.services.emi_engine import summarize_emis
from backend.services.expense_classifier import classify_expense_split
from backend.models.predict import build_daily_expense_series, predict_next_expense
from backend.services.networth_engine import calculate_networth
from backend.services.priority_engine import build_priorities
from backend.services.subscription_engine import get_all_subscriptions
from backend.storage import Storage, bills_db

router = APIRouter()


def build_category_comparison(transactions: pd.DataFrame) -> list:
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


def build_goal_suggestion(metrics: dict, budget_snapshot: dict) -> dict:
    leftover = max(0.0, float(budget_snapshot["global"]["remaining_amount"]))
    suggested = round(min(leftover * 0.45, max(float(metrics["netSavings"]) * 0.3, 0.0)), 2)
    return {
        "recommendedContribution": suggested,
        "message": (
            f"Based on your remaining budget, consider moving Rs{round(suggested):,} toward your top savings goal."
            if suggested > 0
            else "Hold contributions for now and stabilize monthly spending first."
        ),
    }


def _build_metrics_from_data(
    transactions: pd.DataFrame,
    subscriptions: list,
    emi_summary: dict,
    budget_global: dict,
    behavior: dict,
    anomaly: dict,
) -> dict:
    """Build dashboard metrics from already-fetched data, no extra DB reads."""
    income_df = transactions[transactions["amount"] > 0]
    expense_df = transactions[transactions["amount"] < 0].copy()

    total_income = float(income_df["amount"].sum())
    total_expense = abs(float(expense_df["amount"].sum()))
    recurring_commitments = (
        sum(float(s["monthly_cost"]) for s in subscriptions) + float(emi_summary["monthly_load"])
    )
    net_savings = total_income - total_expense - recurring_commitments
    savings_ratio = round((net_savings / total_income * 100) if total_income > 0 else 0, 2)

    daily_expenses = (
        expense_df.groupby("date")["amount"].sum().abs()
        if not expense_df.empty
        else pd.Series(dtype=float)
    )
    volatility = round(float(daily_expenses.std() if len(daily_expenses) > 1 else 0), 2)

    budget_pressure = min(100, float(budget_global.get("usage_percent", 0)))
    health_score = 55 + (savings_ratio * 0.45) - (volatility / max(total_income, 1) * 100) - (budget_pressure * 0.18)
    health_score = max(0, min(100, round(health_score)))

    today = datetime.now()
    day_count = max(1, today.day)
    burn_rate = round(total_expense / day_count, 2)
    savings_growth = round(max(0.0, savings_ratio / max(day_count / 5, 1)), 2)
    lifestyle_inflation = round(max(0.0, (total_expense / max(total_income, 1)) * 7.5), 2)
    runway_months = round(max(0.0, float(budget_global.get("remaining_amount", 0)) / max(burn_rate * 30, 1)), 1)

    credit_score = calculate_credit_score({
        "income": total_income,
        "total_expense": total_expense,
        "savings_ratio": savings_ratio,
        "expense_volatility": volatility,
        "anomaly_count": anomaly.get("count", 0),
    })

    if savings_ratio >= 60 and budget_pressure < 80:
        personality = "Balanced Saver"
    elif budget_pressure >= 90:
        personality = "Pressure Spender"
    elif total_income > 0 and total_expense / max(total_income, 1) < 0.45:
        personality = "Disciplined Planner"
    else:
        personality = "Adaptive Spender"

    return {
        "totalIncome": round(total_income, 2),
        "totalExpense": round(total_expense, 2),
        "netSavings": round(net_savings, 2),
        "totalBalance": round(net_savings + 13000, 2),
        "savingsRatio": savings_ratio,
        "volatility": volatility,
        "healthScore": health_score,
        "budgetUsagePercent": budget_pressure,
        "remainingBudget": round(float(budget_global.get("remaining_amount", 0)), 2),
        "dailyAllowance": round(float(budget_global.get("daily_allowance", 0)), 2),
        "burnRate": burn_rate,
        "savingsGrowth": savings_growth,
        "lifestyleInflation": lifestyle_inflation,
        "runwayMonths": runway_months,
        "financialPersonality": personality,
        "subscriptionLoad": round(sum(float(s["monthly_cost"]) for s in subscriptions), 2),
        "monthlyEmiLoad": round(float(emi_summary["monthly_load"]), 2),
        "netWorth": 0.0,  # filled by Level 2 (networth)
        "assets": 0.0,
        "liabilities": 0.0,
        "fixedExpensePercent": 0.0,
        "variableExpensePercent": 0.0,
        "projectedOutflow": 0.0,
        "fixedTotal": 0.0,
        "variableTotal": 0.0,
        "behaviorProfile": behavior.get("behavior_profile", "balanced"),
        "behaviorVolatility": round(float(behavior.get("spending_volatility", 0)), 2),
        "anomalyCount": anomaly.get("count", 0),
        "creditScore": credit_score,
        "advisoryStrength": 0,
        "trends": {
            "balanceTrend": 4.2,
            "incomeTrend": 12.0,
            "expenseTrend": -2.4,
            "savingsTrend": 1.6,
        },
    }


@router.get("/")
async def get_dashboard():
    # Single DB read — all engines that call Storage.get_transactions() hit the 5s TTL cache
    transactions = Storage.get_transactions()

    # ── Level 1: All independent tasks run in parallel ──────────────────────
    (
        budget_snapshot,
        category_chart,
        subscriptions,
        emi_summary,
        daily_series,
        anomaly,
        behavior,
    ) = await asyncio.gather(
        asyncio.to_thread(build_budget_snapshot, transactions),
        asyncio.to_thread(build_category_comparison, transactions),
        asyncio.to_thread(get_all_subscriptions, transactions),
        asyncio.to_thread(summarize_emis, transactions),
        asyncio.to_thread(build_daily_expense_series, transactions),
        asyncio.to_thread(latest_anomaly_summary, transactions),
        asyncio.to_thread(build_behavior_profile, transactions),
    )

    # Build metrics from pre-fetched data (zero extra DB reads)
    budget_global = budget_snapshot["global"]
    recurring_load = float(emi_summary["monthly_load"]) + sum(float(s["monthly_cost"]) for s in subscriptions)
    metrics = _build_metrics_from_data(transactions, subscriptions, emi_summary, budget_global, behavior, anomaly)

    # ── Level 2: Depends on Level 1 ─────────────────────────────────────────
    (
        expense_split,
        networth,
        cashflow,
        prediction,
    ) = await asyncio.gather(
        asyncio.to_thread(classify_expense_split, transactions, subscriptions, emi_summary, bills_db),
        asyncio.to_thread(calculate_networth, metrics, emi_summary),
        asyncio.to_thread(build_cashflow_timeline, subscriptions, emi_summary, bills_db, transactions),
        asyncio.to_thread(
            predict_next_expense, daily_series, False, True,
            _budget_summary=budget_global,
            _recurring_load=recurring_load,
            _behavior_profile=behavior,
        ),
    )

    # Patch networth into metrics
    metrics.update({
        "netWorth": round(float(networth.get("net_worth", 0)), 2),
        "assets": round(float(networth.get("assets", 0)), 2),
        "liabilities": round(float(networth.get("liabilities", 0)), 2),
        "fixedExpensePercent": round(float(expense_split.get("fixed_percent", 0)), 2),
        "variableExpensePercent": round(float(expense_split.get("variable_percent", 0)), 2),
        "projectedOutflow": round(float(cashflow.get("monthly_outflow_projection", 0)), 2),
        "fixedTotal": round(float(expense_split.get("fixed_total", 0)), 2),
        "variableTotal": round(float(expense_split.get("variable_total", 0)), 2),
    })

    # ── Level 3: Depends on cashflow + budget ───────────────────────────────
    priorities = await asyncio.to_thread(build_priorities, metrics, budget_snapshot, subscriptions, emi_summary, cashflow)

    # Advisory loads async on the frontend via POST /api/smart-advice
    advisory = {"recommended_savings": 0, "advice": [], "behavior_profile": behavior.get("behavior_profile", "balanced")}

    sorted_transactions = transactions.sort_values("date", ascending=False)
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
            "recentTransactions": sorted_transactions.head(5).to_dict(orient="records"),
            "allTransactions": sorted_transactions.to_dict(orient="records"),
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
    """Direct endpoint for real-time Smart Advice generation."""
    advisory = await generate_financial_advice(
        payload.metrics,
        payload.budgeting,
        payload.prediction,
        payload.expenseSplit,
        payload.behavior,
    )
    return {"status": 200, "data": advisory}
