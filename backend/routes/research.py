from fastapi import APIRouter

from backend.services.research_engine import get_research_report

router = APIRouter()


@router.get("/report")
def get_report():
    return {
        "status": 200,
        "data": get_research_report(),
    }
