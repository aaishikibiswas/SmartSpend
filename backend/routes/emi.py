from fastapi import APIRouter
from pydantic import BaseModel

from backend.services.emi_engine import add_emi, get_all_emis, summarize_emis
from backend.services.pipeline import broadcast_snapshot

router = APIRouter()


class EmiCreate(BaseModel):
    name: str
    total_amount: float
    monthly_emi: float
    remaining_months: int
    interest_rate: float | None = None
    due_date: str


@router.get("/")
def list_emis():
    summary = summarize_emis()
    return {
        "status": 200,
        "data": {
            "items": summary["items"],
            "monthly_load": summary["monthly_load"],
            "remaining_liability": summary["remaining_liability"],
        },
    }


@router.post("/")
async def create_emi(payload: EmiCreate):
    item = add_emi(payload.model_dump())
    await broadcast_snapshot(event_type="update", source="emi")
    return {
        "status": 201,
        "data": item,
    }


@router.delete("/{identifier}")
async def delete_emi(identifier: str):
    from backend.services.emi_engine import remove_emi

    remove_emi(identifier)
    await broadcast_snapshot(event_type="update", source="emi")
    return {
        "status": 200,
        "data": {"removed": identifier},
    }
