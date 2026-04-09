from __future__ import annotations

from datetime import datetime

import pandas as pd

from backend.services.budget_engine import get_global_budget_summary
from backend.services.anomaly_engine import latest_anomaly_summary
from backend.services.advisory_engine import generate_financial_advice
from backend.services.behavior_engine import build_behavior_profile
from backend.services.cashflow_engine import build_cashflow_timeline
from backend.services.credit_score_engine import calculate_credit_score
from backend.services.emi_engine import summarize_emis
from backend.services.expense_classifier import classify_expense_split
from backend.services.networth_engine import calculate_networth
from backend.models.predict import build_daily_expense_series, predict_next_expense
from backend.services.subscription_engine import get_all_subscriptions
from backend.storage import Storage
from backend.storage import bills_db


def get_dashboard_analytics() -> dict:
    df = Storage.get_transactions()

    if df.empty:
        emi_summary = summarize_emis()
        networth = calculate_networth({"totalBalance": 0, "netSavings": 0}, emi_summary)
        expense_split = classify_expense_split(df, [], emi_summary, bills_db)
        cashflow = build_cashflow_timeline([], emi_summary, bills_db)
        prediction = predict_next_expense(build_daily_expense_series(df))
        behavior = build_behavior_profile(df)
        advisory = generate_financial_advice({"totalIncome": 0, "netSavings": 0, "savingsRatio": 0}, {"global": {"usage_percent": 0}}, prediction, expense_split, behavior)
        anomaly = latest_anomaly_summary(df)
        credit_score = calculate_credit_score(
            {
                "income": 0,
                "total_expense": 0,
                "savings_ratio": 0,
                "expense_volatility": 0,
                "anomaly_count": anomaly["count"],
            }
        )
        return {
            "totalIncome": 0,
            "totalExpense": 0,
            "netSavings": 0,
            "totalBalance": 0,
            "savingsRatio": 0,
            "volatility": 0,
            "healthScore": 0,
            "budgetUsagePercent": 0,
            "remainingBudget": 0,
            "dailyAllowance": 0,
            "burnRate": 0,
            "savingsGrowth": 0,
            "lifestyleInflation": 0,
            "runwayMonths": 0,
            "financialPersonality": "Balanced Saver",
            "subscriptionLoad": 0,
            "monthlyEmiLoad": round(float(emi_summary["monthly_load"]), 2),
            "netWorth": round(float(networth["net_worth"]), 2),
            "assets": round(float(networth["assets"]), 2),
            "liabilities": round(float(networth["liabilities"]), 2),
            "fixedExpensePercent": round(float(expense_split["fixed_percent"]), 2),
            "variableExpensePercent": round(float(expense_split["variable_percent"]), 2),
            "projectedOutflow": round(float(cashflow["monthly_outflow_projection"]), 2),
            "fixedTotal": round(float(expense_split["fixed_total"]), 2),
            "variableTotal": round(float(expense_split["variable_total"]), 2),
            "behaviorProfile": behavior["behavior_profile"],
            "behaviorVolatility": round(float(behavior["spending_volatility"]), 2),
            "anomalyCount": anomaly["count"],
            "creditScore": credit_score,
            "advisoryStrength": len(advisory["advice"]),
            "trends": {"balanceTrend": 0, "incomeTrend": 0, "expenseTrend": 0, "savingsTrend": 0},
        }

    income_df = df[df["amount"] > 0]
    expense_df = df[df["amount"] < 0].copy()
    subscriptions = get_all_subscriptions(df)
    emi_summary = summarize_emis()

    total_income = float(income_df["amount"].sum())
    total_expense = abs(float(expense_df["amount"].sum()))
    recurring_commitments = sum(float(item["monthly_cost"]) for item in subscriptions) + float(emi_summary["monthly_load"])
    net_savings = total_income - total_expense - recurring_commitments
    savings_ratio = round((net_savings / total_income * 100) if total_income > 0 else 0, 2)

    daily_expenses = expense_df.groupby("date")["amount"].sum().abs() if not expense_df.empty else pd.Series(dtype=float)
    volatility = round(float(daily_expenses.std() if len(daily_expenses) > 1 else 0), 2)

    budget_summary = get_global_budget_summary(df)
    expense_split = classify_expense_split(df, subscriptions, emi_summary, bills_db)
    networth = calculate_networth({"totalBalance": net_savings + 13000, "netSavings": net_savings}, emi_summary)
    cashflow = build_cashflow_timeline(subscriptions, emi_summary, bills_db)
    prediction = predict_next_expense(build_daily_expense_series(df))
    behavior = build_behavior_profile(df)
    advisory = generate_financial_advice(
        {"totalIncome": total_income, "netSavings": net_savings, "savingsRatio": savings_ratio},
        {"global": budget_summary},
        prediction,
        expense_split,
        behavior,
    )
    anomaly = latest_anomaly_summary(df)
    credit_score = calculate_credit_score(
        {
            "income": total_income,
            "total_expense": total_expense,
            "savings_ratio": savings_ratio,
            "expense_volatility": volatility,
            "anomaly_count": anomaly["count"],
        }
    )
    budget_pressure = min(100, float(budget_summary["usage_percent"]))
    health_score = 55 + (savings_ratio * 0.45) - (volatility / max(total_income, 1) * 100) - (budget_pressure * 0.18)
    health_score = max(0, min(100, round(health_score)))
    today = datetime.now()
    day_count = max(1, today.day)
    burn_rate = round(total_expense / day_count, 2)
    savings_growth = round(max(0.0, savings_ratio / max(day_count / 5, 1)), 2)
    lifestyle_inflation = round(max(0.0, (total_expense / max(total_income, 1)) * 7.5), 2)
    runway_months = round(max(0.0, (float(budget_summary["remaining_amount"]) / max(burn_rate * 30, 1))), 1)

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
        "budgetUsagePercent": round(float(budget_summary["usage_percent"]), 2),
        "remainingBudget": round(float(budget_summary["remaining_amount"]), 2),
        "dailyAllowance": round(float(budget_summary["daily_allowance"]), 2),
        "burnRate": burn_rate,
        "savingsGrowth": savings_growth,
        "lifestyleInflation": lifestyle_inflation,
        "runwayMonths": runway_months,
        "financialPersonality": personality,
        "subscriptionLoad": round(sum(float(item["monthly_cost"]) for item in subscriptions), 2),
        "monthlyEmiLoad": round(float(emi_summary["monthly_load"]), 2),
        "netWorth": round(float(networth["net_worth"]), 2),
        "assets": round(float(networth["assets"]), 2),
        "liabilities": round(float(networth["liabilities"]), 2),
        "fixedExpensePercent": round(float(expense_split["fixed_percent"]), 2),
        "variableExpensePercent": round(float(expense_split["variable_percent"]), 2),
        "projectedOutflow": round(float(cashflow["monthly_outflow_projection"]), 2),
        "fixedTotal": round(float(expense_split["fixed_total"]), 2),
        "variableTotal": round(float(expense_split["variable_total"]), 2),
        "behaviorProfile": behavior["behavior_profile"],
        "behaviorVolatility": round(float(behavior["spending_volatility"]), 2),
        "anomalyCount": anomaly["count"],
        "creditScore": credit_score,
        "advisoryStrength": len(advisory["advice"]),
        "trends": {
            "balanceTrend": 4.2,
            "incomeTrend": 12.0,
            "expenseTrend": -2.4,
            "savingsTrend": 1.6,
        },
    }
