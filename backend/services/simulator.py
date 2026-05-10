from __future__ import annotations

from backend.services.behavior_engine import build_behavior_profile
from backend.services.cashflow_engine import build_cashflow_timeline
from backend.services.emi_engine import summarize_emis
from backend.services.expense_classifier import classify_expense_split
from backend.services.networth_engine import calculate_networth
from backend.services.priority_engine import build_priorities
from backend.services.subscription_engine import get_all_subscriptions
from backend.models.predict import build_daily_expense_series, predict_next_expense
from backend.storage import Storage


def simulate_finances(transactions, input_data: dict) -> dict:
    income_adjustment = float(input_data.get("income_adjustment", 0) or 0)
    expense_adjustment = float(input_data.get("expense_adjustment", 0) or 0)
    months = max(1, int(input_data.get("months", 6) or 6))

    rows = transactions.to_dict(orient="records") if hasattr(transactions, "to_dict") else list(transactions)
    total_income = sum(float(t["amount"]) for t in rows if float(t.get("amount", 0)) > 0 or str(t.get("type", "")).lower() == "credit")
    total_expense = sum(abs(float(t["amount"])) for t in rows if float(t.get("amount", 0)) < 0 or str(t.get("type", "")).lower() in {"debit", "expense"})

    new_income = round(total_income + income_adjustment, 2)
    new_expense = round(max(total_expense + expense_adjustment, 0.0), 2)
    monthly_savings = round(new_income - new_expense, 2)
    projected_savings = round(monthly_savings * months, 2)

    subscriptions = get_all_subscriptions(transactions)
    emi_summary = summarize_emis(transactions)
    bills = Storage.get_bills()
    expense_split = classify_expense_split(transactions, subscriptions, emi_summary, bills)
    baseline_behavior = build_behavior_profile(transactions)
    variable_adjustment = max(new_expense - float(expense_split["fixed_total"]), 0.0)
    simulated_total = float(expense_split["fixed_total"]) + variable_adjustment
    simulated_split = {
        "fixed_total": round(float(expense_split["fixed_total"]), 2),
        "variable_total": round(variable_adjustment, 2),
        "fixed_percent": round((float(expense_split["fixed_total"]) / simulated_total) * 100, 2) if simulated_total else 0.0,
        "variable_percent": round((variable_adjustment / simulated_total) * 100, 2) if simulated_total else 0.0,
        "breakdown": [
            {"name": "Fixed", "amount": round(float(expense_split["fixed_total"]), 2)},
            {"name": "Variable", "amount": round(variable_adjustment, 2)},
        ],
    }
    simulated_behavior_profile = baseline_behavior.get("behavior_profile", "balanced")
    if simulated_split["fixed_percent"] > 70:
        simulated_behavior_profile = "high fixed burden"
    elif simulated_split["variable_percent"] > 70:
        simulated_behavior_profile = "high variable spending"
    else:
        simulated_behavior_profile = "balanced"

    updated_metrics = {
        "totalIncome": new_income,
        "totalExpense": new_expense,
        "netSavings": monthly_savings,
        "totalBalance": round(monthly_savings + 13000, 2),
        "savingsRatio": round((monthly_savings / new_income * 100) if new_income > 0 else 0, 2),
        "volatility": 0,
        "healthScore": max(0, min(100, round(55 + ((monthly_savings / max(new_income, 1)) * 45)))),
        "budgetUsagePercent": round((new_expense / max(new_income, 1)) * 100, 2) if new_income > 0 else 0,
        "remainingBudget": monthly_savings,
        "dailyAllowance": round(monthly_savings / 30, 2),
        "burnRate": round(new_expense / 30, 2),
        "savingsGrowth": 0,
        "lifestyleInflation": 0,
        "runwayMonths": round(max(0, projected_savings) / max(new_expense, 1), 1),
        "financialPersonality": simulated_behavior_profile,
        "subscriptionLoad": round(sum(float(item["monthly_cost"]) for item in subscriptions), 2),
        "monthlyEmiLoad": round(float(emi_summary["monthly_load"]), 2),
        "fixedExpensePercent": simulated_split["fixed_percent"],
        "variableExpensePercent": simulated_split["variable_percent"],
    }
    cashflow = build_cashflow_timeline(subscriptions, emi_summary, bills, transactions)
    networth = calculate_networth({"totalBalance": projected_savings + 13000, "netSavings": projected_savings}, emi_summary)
    updated_metrics.update(
        {
            "netWorth": round(float(networth["net_worth"]), 2),
            "assets": round(float(networth["assets"]), 2),
            "liabilities": round(float(networth["liabilities"]), 2),
            "projectedOutflow": round(float(cashflow["monthly_outflow_projection"]), 2),
            "trends": {"balanceTrend": 0, "incomeTrend": 0, "expenseTrend": 0, "savingsTrend": 0},
        }
    )
    baseline_prediction = predict_next_expense(build_daily_expense_series(transactions))
    if monthly_savings < 0 or projected_savings < 0:
        risk_level = "High"
    elif baseline_prediction.get("risk_level") == "High" or monthly_savings < (new_income * 0.1):
        risk_level = "Medium"
    else:
        risk_level = "Low"

    return {
        "new_income": new_income,
        "new_expense": new_expense,
        "monthly_savings": monthly_savings,
        "projected_savings": projected_savings,
        "risk_level": risk_level,
        "simulated_prediction": {
            "predicted_expense": round(max(new_expense / max(months, 1), 0.0), 2),
            "risk_level": risk_level,
            "trend_direction": "upward" if expense_adjustment > 0 else "downward" if expense_adjustment < 0 else baseline_prediction.get("trend_direction", "stable"),
            "confidence_score": baseline_prediction.get("confidence_score", 0.42),
            "behavior_profile": simulated_behavior_profile,
            "model_contributions": baseline_prediction.get("model_contributions", {}),
            "shap_explanations": baseline_prediction.get("shap_explanations", {}),
        },
        "risk_change": {
            "from": baseline_prediction.get("risk_level", "Low"),
            "to": risk_level,
        },
        "behavior_profile": simulated_behavior_profile,
        "expense_split": simulated_split,
        "updated_metrics": updated_metrics,
        "networth": networth,
        "cashflow": cashflow,
        "priorities": build_priorities(updated_metrics, {"global": {"remaining_amount": monthly_savings, "usage_percent": updated_metrics["budgetUsagePercent"]}}, subscriptions, emi_summary, cashflow),
        "months": months,
    }
