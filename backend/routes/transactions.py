from fastapi import APIRouter
from pydantic import BaseModel

from backend.services.categorizer import categorize_transaction
from backend.services.pipeline import process_live_transaction

router = APIRouter()


class TransactionCreate(BaseModel):
    date: str
    merchant: str
    category: str | None = None
    amount: float


@router.post("/")
async def add_transaction(payload: TransactionCreate):
    transaction = {
        "date": payload.date,
        "merchant": payload.merchant.strip().title(),
        "category": payload.category.strip() if payload.category and payload.category.strip() else categorize_transaction(payload.merchant, amount=payload.amount, date=payload.date),
        "amount": payload.amount,
        "type": "income" if payload.amount > 0 else "expense",
        "language": "English",
    }

    await process_live_transaction(transaction)

    return {
        "status": 201,
        "data": transaction,
    }
