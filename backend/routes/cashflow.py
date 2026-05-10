from fastapi import APIRouter

from backend.services.cashflow_engine import build_cashflow_timeline
from backend.services.emi_engine import summarize_emis
from backend.services.subscription_engine import get_all_subscriptions
from backend.storage import Storage

router = APIRouter()


@router.get("/")
def get_cashflow():
    transactions = Storage.get_transactions()
    data = build_cashflow_timeline(get_all_subscriptions(transactions), summarize_emis(), Storage.get_bills())
    return {
        "status": 200,
        "data": data,
    }
