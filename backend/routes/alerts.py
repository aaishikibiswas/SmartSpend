from fastapi import APIRouter
from backend.services.alert_engine import get_all_alerts

router = APIRouter()

@router.get("/")
def get_alerts():
    return {"status": 200, "data": get_all_alerts()}
