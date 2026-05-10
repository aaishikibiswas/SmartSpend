from fastapi import APIRouter

from backend.services.emi_engine import summarize_emis
from backend.services.expense_classifier import classify_expense_split
from backend.services.subscription_engine import get_all_subscriptions
from backend.storage import Storage

router = APIRouter()


@router.get("/")
def get_expense_split():
    transactions = Storage.get_transactions()
    data = classify_expense_split(transactions, get_all_subscriptions(transactions), summarize_emis(transactions), Storage.get_bills())
    return {
        "status": 200,
        "data": data,
    }
