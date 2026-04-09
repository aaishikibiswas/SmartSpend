from fastapi import APIRouter

from backend.services.analytics import get_dashboard_analytics
from backend.services.budget_engine import build_budget_snapshot
from backend.services.cashflow_engine import build_cashflow_timeline
from backend.services.emi_engine import summarize_emis
from backend.services.priority_engine import build_priorities
from backend.services.subscription_engine import get_all_subscriptions
from backend.storage import Storage, bills_db

router = APIRouter()


@router.get("/")
def get_priorities():
    transactions = Storage.get_transactions()
    subscriptions = get_all_subscriptions(transactions)
    emi_summary = summarize_emis()
    cashflow = build_cashflow_timeline(subscriptions, emi_summary, bills_db)
    actions = build_priorities(get_dashboard_analytics(), build_budget_snapshot(transactions), subscriptions, emi_summary, cashflow)
    return {
        "status": 200,
        "data": actions,
    }
