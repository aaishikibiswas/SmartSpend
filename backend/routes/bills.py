from fastapi import APIRouter
from backend.storage import Storage
from backend.services.pipeline import broadcast_snapshot
from pydantic import BaseModel

router = APIRouter()

class BillCreate(BaseModel):
    name: str
    amount: float
    due: str
    icon: str = "Zap"
    color: str = "blue"

@router.get("/")
def get_bills():
    return {"status": 200, "data": Storage.get_bills()}

@router.post("/")
async def add_bill(bill: BillCreate):
    new_bill = Storage.add_bill(bill.dict())
    await broadcast_snapshot(event_type="update", source="bills")
    return {"status": 201, "data": new_bill}


@router.delete("/{identifier}")
async def remove_bill(identifier: str):
    Storage.remove_bill(identifier)
    await broadcast_snapshot(event_type="update", source="bills")
    return {"status": 200, "data": {"removed": identifier}}
