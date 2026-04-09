from fastapi import APIRouter
from pydantic import BaseModel, Field

from backend.services.decision_engine import evaluate_purchase

router = APIRouter()


class DecisionPayload(BaseModel):
    item_name: str
    price: float = Field(ge=0)


@router.post("/")
def get_purchase_decision(payload: DecisionPayload):
    return {
        "status": 200,
        "data": evaluate_purchase(payload.item_name, payload.price),
    }
