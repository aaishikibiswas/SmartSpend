from __future__ import annotations

from typing import Any

from backend.models.predict import build_daily_expense_series, generate_prophet_forecast, predict_next_expense
from backend.services.alert_engine import get_all_alerts
from backend.services.analytics import get_dashboard_analytics
from backend.services.budget_engine import get_budget_snapshot
from backend.services.goal_engine import get_all_goals
from backend.storage import Storage, bills_db


def _format_currency(value: float) -> str:
    return f"Rs{round(float(value), 2):,.2f}".replace(".00", "")


def _top_category(expenses_by_category: dict[str, float]) -> tuple[str, float] | None:
    if not expenses_by_category:
        return None
    name = max(expenses_by_category, key=expenses_by_category.get)
    return name, expenses_by_category[name]


def _expense_context() -> dict[str, Any]:
    df = Storage.get_transactions()
    expenses_df = df[df["amount"] < 0].copy()
    income_df = df[df["amount"] > 0].copy()

    if not expenses_df.empty:
        expenses_df["spend"] = expenses_df["amount"].abs()
        category_spend = expenses_df.groupby("category")["spend"].sum().sort_values(ascending=False).to_dict()
        merchant_spend = expenses_df.groupby("merchant")["spend"].sum().sort_values(ascending=False).to_dict()
        largest_row = expenses_df.loc[expenses_df["spend"].idxmax()].to_dict()
    else:
        category_spend = {}
        merchant_spend = {}
        largest_row = None

    recent_rows = df.sort_values("date", ascending=False).head(5).to_dict(orient="records") if not df.empty else []

    return {
        "df": df,
        "expenses_df": expenses_df,
        "income_df": income_df,
        "category_spend": category_spend,
        "merchant_spend": merchant_spend,
        "largest_row": largest_row,
        "recent_rows": recent_rows,
    }


def _suggestions() -> list[str]:
    return [
        "Which category am I spending the most on?",
        "What is my next predicted expense?",
        "Do I have any budget alerts right now?",
        "What are my top 3 recent transactions?",
    ]


def answer_finance_query(question: str) -> dict[str, Any]:
    q = (question or "").strip()
    lowered = q.lower()

    metrics = get_dashboard_analytics()
    budget = get_budget_snapshot(Storage.get_transactions())
    alerts = get_all_alerts()
    goals = get_all_goals()
    prediction = predict_next_expense(build_daily_expense_series(Storage.get_transactions()))
    forecast = generate_prophet_forecast(Storage.get_transactions(), days=15)
    ctx = _expense_context()

    top_category = _top_category(ctx["category_spend"])
    top_merchant = _top_category(ctx["merchant_spend"])

    category_aliases = {item["name"].lower(): item["name"] for item in budget["categories"]}
    mentioned_category = next((actual for key, actual in category_aliases.items() if key in lowered), None)

    if not q:
        return {
            "answer": "Ask about your spending, forecasts, alerts, goals, bills, or recent transactions and I will answer from your uploaded data.",
            "suggestions": _suggestions(),
        }

    if "category" in lowered and ("most" in lowered or "highest" in lowered or "top" in lowered):
        if top_category is None:
            answer = "I do not have expense data yet. Upload a statement first so I can compare your spending categories."
        else:
            answer = f"Your highest spending category is {top_category[0]} at {_format_currency(top_category[1])}. "
            if top_merchant:
                answer += f"Your top merchant overall is {top_merchant[0]} at {_format_currency(top_merchant[1])}."
        return {"answer": answer, "suggestions": _suggestions()}

    if mentioned_category and ("spent" in lowered or "spending" in lowered or "budget" in lowered):
        spent = float(ctx["category_spend"].get(mentioned_category, 0))
        category_budget_entry = next((item for item in budget["categories"] if item["name"] == mentioned_category), None)
        budget_amount = float(category_budget_entry["allocated_amount"]) if category_budget_entry else 0.0
        remaining = max(0.0, budget_amount - spent)
        return {
            "answer": f"You have spent {_format_currency(spent)} on {mentioned_category}. Your configured budget is {_format_currency(budget_amount)}, so you have {_format_currency(remaining)} remaining.",
            "suggestions": _suggestions(),
        }

    if "top merchant" in lowered or "largest merchant" in lowered:
        if top_merchant is None:
            return {"answer": "I do not have enough expense data yet to rank merchants.", "suggestions": _suggestions()}
        return {
            "answer": f"Your top merchant by spend is {top_merchant[0]} at {_format_currency(top_merchant[1])}.",
            "suggestions": _suggestions(),
        }

    if "largest transaction" in lowered or "biggest expense" in lowered or "highest transaction" in lowered:
        largest = ctx["largest_row"]
        if not largest:
            return {"answer": "I do not have expense data yet to identify the largest transaction.", "suggestions": _suggestions()}
        return {
            "answer": f"Your largest expense is {largest['merchant']} in {largest['category']} for {_format_currency(abs(float(largest['amount'])))} on {largest['date']}.",
            "suggestions": _suggestions(),
        }

    if "total expense" in lowered or "how much have i spent" in lowered or ("spent" in lowered and "total" in lowered):
        return {
            "answer": f"Your total expense from the uploaded data is {_format_currency(metrics['totalExpense'])}. Your total income is {_format_currency(metrics['totalIncome'])}, leaving net savings of {_format_currency(metrics['netSavings'])}.",
            "suggestions": _suggestions(),
        }

    if "income" in lowered:
        return {
            "answer": f"Your total income is {_format_currency(metrics['totalIncome'])}. Your current savings ratio is {metrics['savingsRatio']}%.",
            "suggestions": _suggestions(),
        }

    if "save" in lowered or "savings" in lowered or "surplus" in lowered:
        return {
            "answer": f"You currently have net savings of {_format_currency(metrics['netSavings'])}. That is a savings ratio of {metrics['savingsRatio']}% based on the uploaded transactions.",
            "suggestions": _suggestions(),
        }

    if "next predicted expense" in lowered or "prediction" in lowered or "forecast" in lowered:
        return {
            "answer": f"Your next predicted expense is {_format_currency(prediction['predicted_expense'])} with a {prediction['risk_level']} risk level. The 15-day forecast peaks around {forecast['peakAlert']['day']} at {_format_currency(forecast['peakAlert']['amount'])}.",
            "suggestions": _suggestions(),
        }

    if "afford" in lowered or "can i buy" in lowered or "can i afford" in lowered:
        remaining_monthly = max(0.0, float(budget["global"]["remaining_amount"]))
        safe_buffer = max(0.0, remaining_monthly - float(prediction["predicted_expense"]))
        if metrics["netSavings"] <= 0:
            answer = f"I would be careful. Your current net savings are {_format_currency(metrics['netSavings'])}, so you should avoid optional spending until income improves."
        else:
            answer = (
                f"Based on your uploaded data, you still have about {_format_currency(remaining_monthly)} left within your monthly budget. "
                f"After accounting for your next predicted expense of {_format_currency(prediction['predicted_expense'])}, your safer buffer is about {_format_currency(safe_buffer)}."
            )
        return {"answer": answer, "suggestions": _suggestions()}

    if "alert" in lowered or "warning" in lowered:
        if not alerts:
            return {"answer": "You do not have any active alerts right now.", "suggestions": _suggestions()}
        alert = alerts[0]
        return {
            "answer": f"You currently have {len(alerts)} active alerts. The most recent one is '{alert['title']}' and it says: {alert['message']}",
            "suggestions": _suggestions(),
        }

    if "goal" in lowered:
        if not goals:
            return {"answer": "You do not have any goals configured right now.", "suggestions": _suggestions()}
        top_goal = max(goals, key=lambda item: (item["achieved"] / item["target"]) if item["target"] else 0)
        progress = round((top_goal["achieved"] / top_goal["target"]) * 100) if top_goal["target"] else 0
        return {
            "answer": f"Your most advanced goal is {top_goal['name']} at {progress}% complete. You have saved {_format_currency(top_goal['achieved'])} out of {_format_currency(top_goal['target'])}.",
            "suggestions": _suggestions(),
        }

    if "bill" in lowered or "due" in lowered:
        if not bills_db:
            return {"answer": "You do not have any bill reminders configured right now.", "suggestions": _suggestions()}
        next_bill = bills_db[0]
        return {
            "answer": f"Your next bill reminder is {next_bill['name']} for {_format_currency(next_bill['amount'])} and it is marked as {next_bill['due']}.",
            "suggestions": _suggestions(),
        }

    if "recent transaction" in lowered or "recent spending" in lowered or "recent expenses" in lowered:
        if not ctx["recent_rows"]:
            return {"answer": "I do not have recent transactions yet. Upload a statement first.", "suggestions": _suggestions()}
        top_three = ctx["recent_rows"][:3]
        summary = "; ".join(
            f"{row['merchant']} on {row['date']} for {_format_currency(abs(float(row['amount'])))}"
            for row in top_three
        )
        return {
            "answer": f"Your 3 most recent transactions are: {summary}.",
            "suggestions": _suggestions(),
        }

    return {
        "answer": (
            f"From your current data: income is {_format_currency(metrics['totalIncome'])}, expenses are {_format_currency(metrics['totalExpense'])}, "
            f"net savings are {_format_currency(metrics['netSavings'])}, and your next predicted expense is {_format_currency(prediction['predicted_expense'])}. "
            "Ask me about top categories, alerts, goals, recent transactions, bills, budgets, or forecasts."
        ),
        "suggestions": _suggestions(),
    }
