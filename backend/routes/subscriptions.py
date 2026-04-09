from fastapi import APIRouter
from pydantic import BaseModel

from backend.services.pipeline import broadcast_snapshot
from backend.services.subscription_engine import add_subscription, get_all_subscriptions, remove_subscription as remove_subscription_entry
from backend.storage import Storage

router = APIRouter()


class SubscriptionCreate(BaseModel):
    name: str
    monthly_cost: float
    frequency: str = "Monthly"
    last_charge_date: str
    next_due_date: str


@router.get("/")
def get_subscriptions():
    subscriptions = get_all_subscriptions(Storage.get_transactions())
    return {
        "status": 200,
        "data": subscriptions,
    }


@router.post("/")
async def create_subscription(payload: SubscriptionCreate):
    item = add_subscription(payload.model_dump())
    await broadcast_snapshot(event_type="update", source="subscriptions")
    return {
        "status": 201,
        "data": item,
    }


@router.delete("/{name}")
async def remove_subscription(name: str):
    remove_subscription_entry(name)
    await broadcast_snapshot(event_type="update", source="subscriptions")
    return {
        "status": 200,
        "data": {"removed": name},
    }
