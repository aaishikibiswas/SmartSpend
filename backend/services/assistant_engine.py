from __future__ import annotations

from typing import Any

from backend.models.predict import build_daily_expense_series, generate_prophet_forecast, predict_next_expense
from backend.services.alert_engine import get_all_alerts
from backend.services.analytics import get_dashboard_analytics
from backend.services.budget_engine import get_budget_snapshot
from backend.services.cashflow_engine import build_cashflow_timeline
from backend.services.emi_engine import summarize_emis
from backend.services.expense_classifier import classify_expense_split
from backend.services.goal_engine import get_all_goals
from backend.services.subscription_engine import get_all_subscriptions
from backend.storage import Storage


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
        "How can I improve my savings this month?",
        "Which category am I spending the most on?",
        "Do I have any budget alerts right now?",
        "What recurring payments should I review?",
    ]


def _line_items(items: list[str]) -> str:
    return "; ".join(item for item in items if item)


def answer_finance_query(question: str, history: list[dict[str, str]] | None = None) -> dict[str, Any]:
    q = (question or "").strip()
    lowered = q.lower()
    history = history or []

    metrics = get_dashboard_analytics()
    budget = get_budget_snapshot(Storage.get_transactions())
    alerts = get_all_alerts()
    goals = get_all_goals()
    subscriptions = get_all_subscriptions(Storage.get_transactions())
    emi_summary = summarize_emis()
    bills = Storage.get_bills()
    expense_split = classify_expense_split(Storage.get_transactions(), subscriptions, emi_summary, bills)
    cashflow = build_cashflow_timeline(subscriptions, emi_summary, bills)
    prediction = predict_next_expense(build_daily_expense_series(Storage.get_transactions()))
    forecast = generate_prophet_forecast(Storage.get_transactions(), days=15)
    ctx = _expense_context()

    top_category = _top_category(ctx["category_spend"])
    top_merchant = _top_category(ctx["merchant_spend"])

    category_aliases = {item["name"].lower(): item["name"] for item in budget["categories"]}
    mentioned_category = next((actual for key, actual in category_aliases.items() if key in lowered), None)

    recent_history = [item for item in history if item.get("text")]
    last_user_prompt = next((item["text"] for item in reversed(recent_history) if item.get("role") == "user" and item.get("text", "").strip().lower() != lowered), "")
    last_ai_reply = next((item["text"] for item in reversed(recent_history) if item.get("role") == "ai"), "")
    follow_up = lowered in {"why", "why?", "how", "how?", "show me how", "show me how?", "what should i do first", "what should i do first?", "what next", "then what", "explain more", "tell me more"}

    if follow_up:
        reference = f"{last_user_prompt} {last_ai_reply}".lower()
        if any(token in reference for token in ["more money", "income", "save", "savings", "surplus"]):
            steps: list[str] = []
            if top_category:
                steps.append(f"cap {top_category[0]} spending first")
            if subscriptions:
                steps.append("remove or downgrade one recurring subscription this week")
            if emi_summary["monthly_load"] > 0:
                steps.append("do not commit to new discretionary spending before EMI dates")
            steps.append("move a fixed amount to savings right after income lands")
            return {
                "answer": "Start with this order: " + "; ".join(steps[:4]) + ". If you want, I can next break this into a weekly action plan from your current numbers.",
                "suggestions": [
                    "Give me a weekly action plan",
                    "Which subscriptions should I review?",
                    "How much can I safely move to savings?",
                    "Which category am I spending the most on?",
                ],
            }
        if any(token in reference for token in ["subscription", "recurring"]):
            return {
                "answer": "I would start by cancelling the lowest-value recurring payment first, then watch whether that monthly amount can be redirected to savings or your emergency fund instead of getting re-spent.",
                "suggestions": [
                    "Which subscriptions should I review?",
                    "How much can I safely move to savings?",
                    "What is my monthly EMI load?",
                    "What does my cash flow look like this month?",
                ],
            }
        if any(token in reference for token in ["emi", "loan"]):
            return {
                "answer": "The safest move is to protect EMI cash flow first, then reduce optional variable spending around those due dates. That lowers financial stress faster than making aggressive new commitments.",
                "suggestions": [
                    "What does my cash flow look like this month?",
                    "How much am I spending on fixed expenses?",
                    "How can I improve my savings this month?",
                    "Can I afford a new purchase right now?",
                ],
            }
        if any(token in reference for token in ["fixed expense", "variable expense", "expense split"]):
            return {
                "answer": "Your flexible control is mainly in the variable side. Fixed expenses change slower, so the faster win is reducing the biggest variable category and recurring non-essential payments first.",
                "suggestions": [
                    "Which category am I spending the most on?",
                    "What recurring payments should I review?",
                    "Do I have any budget alerts right now?",
                    "How can I improve my savings this month?",
                ],
            }

    if any(token in lowered for token in ["make more money", "increase income", "earn more", "grow income", "more money"]):
        ideas: list[str] = []
        if top_category and top_category[1] > max(metrics["totalExpense"] * 0.25, 1):
            ideas.append(f"trim {top_category[0]} first because it is your biggest leak at {_format_currency(top_category[1])}")
        if subscriptions:
            monthly_subscriptions = sum(float(item.get("monthly_cost", 0)) for item in subscriptions)
            ideas.append(f"review subscriptions worth about {_format_currency(monthly_subscriptions)} per month")
        if emi_summary["monthly_load"] > 0:
            ideas.append(f"protect cash flow around your EMI load of {_format_currency(emi_summary['monthly_load'])}")
        if metrics["netSavings"] > 0:
            ideas.append(f"redirect at least {_format_currency(max(metrics['netSavings'] * 0.2, 3000))} of this month's surplus into a goal or emergency fund")
        if budget["global"]["remaining_amount"] > 0:
            ideas.append(f"use your remaining budget of {_format_currency(budget['global']['remaining_amount'])} more intentionally instead of letting it disappear in small spends")
        answer = "To improve your finances, focus on higher-impact moves instead of random cuts: " + _line_items(ideas[:4]) + "."
        return {
            "answer": answer,
            "suggestions": [
                "Which subscriptions should I review?",
                "How can I reduce my biggest expense category?",
                "What is my monthly EMI load?",
                "How much can I safely move to savings?",
            ],
        }

    if any(token in lowered for token in ["improve my savings", "save more", "reduce spending", "cut spending", "spend less"]):
        guidance: list[str] = []
        if top_category:
            guidance.append(f"start with {top_category[0]}, where you have spent {_format_currency(top_category[1])}")
        guidance.append(f"your current daily allowance is {_format_currency(budget['global']['daily_allowance'])}")
        if alerts:
            guidance.append(f"resolve your top alert: {alerts[0]['title']}")
        if subscriptions:
            guidance.append(f"check recurring subscriptions before cutting essentials")
        return {
            "answer": "The fastest way to save more right now is to " + _line_items(guidance[:4]) + ".",
            "suggestions": [
                "Which category am I spending the most on?",
                "Do I have any budget alerts right now?",
                "What recurring payments should I review?",
                "What is my next predicted expense?",
            ],
        }

    if any(token in lowered for token in ["subscription", "recurring payment", "recurring payments", "subscriptions"]):
        if not subscriptions:
            return {"answer": "I do not see any active subscriptions right now.", "suggestions": _suggestions()}
        top_subscriptions = sorted(subscriptions, key=lambda item: float(item.get("monthly_cost", 0)), reverse=True)[:3]
        summary = "; ".join(
            f"{item['name']} at {_format_currency(item['monthly_cost'])} per month, next due {item['next_due_date']}"
            for item in top_subscriptions
        )
        return {
            "answer": f"Your recurring subscriptions to review are: {summary}.",
            "suggestions": [
                "What is my monthly EMI load?",
                "How much am I spending on fixed expenses?",
                "Which category am I spending the most on?",
                "Do I have any budget alerts right now?",
            ],
        }

    if "emi" in lowered or "loan" in lowered:
        if not emi_summary["items"]:
            return {"answer": "I do not see any EMI liabilities right now.", "suggestions": _suggestions()}
        top_emi = sorted(emi_summary["items"], key=lambda item: float(item.get("monthly_emi", 0)), reverse=True)[0]
        return {
            "answer": f"Your total monthly EMI load is {_format_currency(emi_summary['monthly_load'])}. The largest EMI is {top_emi['name']} at {_format_currency(top_emi['monthly_emi'])} per month with {top_emi['remaining_months']} months remaining.",
            "suggestions": [
                "How much am I spending on fixed expenses?",
                "What recurring payments should I review?",
                "Can I afford a new purchase right now?",
                "What does my cash flow look like this month?",
            ],
        }

    if "fixed expense" in lowered or "variable expense" in lowered or "expense split" in lowered:
        return {
            "answer": f"Your fixed expenses are about {_format_currency(expense_split['fixed_total'])} ({round(expense_split['fixed_percent'])}%) and your variable expenses are about {_format_currency(expense_split['variable_total'])} ({round(expense_split['variable_percent'])}%).",
            "suggestions": [
                "What recurring payments should I review?",
                "How can I improve my savings this month?",
                "Which category am I spending the most on?",
                "Do I have any budget alerts right now?",
            ],
        }

    if "cash flow" in lowered or "upcoming payments" in lowered:
        upcoming = cashflow.get("upcoming_payments", [])[:3]
        if not upcoming:
            return {"answer": "I do not see any upcoming bills, subscriptions, or EMIs right now.", "suggestions": _suggestions()}
        summary = "; ".join(f"{item['name']} on {item['date']} for {_format_currency(item['amount'])}" for item in upcoming)
        return {
            "answer": f"Your nearest scheduled outflows are: {summary}. Your monthly projected outflow is {_format_currency(cashflow['monthly_outflow_projection'])}.",
            "suggestions": [
                "What is my monthly EMI load?",
                "Do I have any bill reminders right now?",
                "Can I afford a new purchase right now?",
                "How can I improve my savings this month?",
            ],
        }

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
        if not bills:
            return {"answer": "You do not have any bill reminders configured right now.", "suggestions": _suggestions()}
        next_bill = bills[0]
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
            f"Here is the quickest summary from your live SmartSpend data: income {_format_currency(metrics['totalIncome'])}, expenses {_format_currency(metrics['totalExpense'])}, "
            f"net savings {_format_currency(metrics['netSavings'])}, monthly budget left {_format_currency(budget['global']['remaining_amount'])}, "
            f"next predicted expense {_format_currency(prediction['predicted_expense'])}, and fixed expense share {round(expense_split['fixed_percent'])}%. "
            "Ask me something specific about savings, subscriptions, EMIs, alerts, bills, affordability, or your top spending areas and I will answer directly from your data."
        ),
        "suggestions": _suggestions(),
    }
