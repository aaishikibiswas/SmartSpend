from fastapi import APIRouter
from pydantic import BaseModel

from backend.services.simulator import simulate_finances
from backend.storage import Storage

router = APIRouter()


class SimulationRequest(BaseModel):
    income_adjustment: float = 0
    expense_adjustment: float = 0
    months: int = 6


@router.post("/")
def simulate(payload: SimulationRequest):
    data = simulate_finances(Storage.get_transactions(), payload.model_dump())
    return {
        "status": 200,
        "data": data,
    }
