import asyncio

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict

from backend.services.categorizer import fast_categorize_transaction
from backend.services.pipeline import process_live_transaction

router = APIRouter()


class TransactionCreate(BaseModel):
    model_config = ConfigDict(extra="allow")

    date: str
    merchant: str
    category: str | None = None
    amount: float


@router.post("/")
async def add_transaction(payload: TransactionCreate):
    extras = {
        key: value
        for key, value in payload.model_extra.items()
        if key not in {"date", "merchant", "category", "amount"} and value is not None
    }
    transaction = {
        "date": payload.date,
        "merchant": payload.merchant.strip().title(),
        "category": payload.category.strip() if payload.category and payload.category.strip() else fast_categorize_transaction(payload.merchant),
        "amount": payload.amount,
        "type": "income" if payload.amount > 0 else "expense",
        "language": "English",
        **extras,
    }

    # Respond fast for manual add flow; run refresh/broadcast work in background.
    asyncio.create_task(process_live_transaction(transaction))

    return {
        "status": 201,
        "data": transaction,
    }
