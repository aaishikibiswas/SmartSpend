from fastapi import APIRouter
from pydantic import BaseModel, Field

from backend.services.llm_client import ask_finance_query

router = APIRouter()

class AssistantQuery(BaseModel):
    session_id: str = Field(default="default")
    question: str

@router.post("/query")
async def query_assistant(payload: AssistantQuery):
    result = await ask_finance_query(payload.session_id, payload.question)
    return {
        "status": 200,
        "data": result,
    }
