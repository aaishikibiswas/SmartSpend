from fastapi import APIRouter
from pydantic import BaseModel

from backend.services.assistant_engine import answer_finance_query

router = APIRouter()


class AssistantQuery(BaseModel):
    question: str


@router.post("/query")
def query_assistant(payload: AssistantQuery):
    result = answer_finance_query(payload.question)
    return {
        "status": 200,
        "data": result,
    }
