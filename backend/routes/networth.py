from fastapi import APIRouter

from backend.services.analytics import get_dashboard_analytics
from backend.services.emi_engine import summarize_emis
from backend.services.networth_engine import calculate_networth

router = APIRouter()


@router.get("/")
def get_networth():
    data = calculate_networth(get_dashboard_analytics(), summarize_emis())
    return {
        "status": 200,
        "data": data,
    }

