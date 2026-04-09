from fastapi import APIRouter
from backend.services.goal_engine import get_all_goals, create_goal
from pydantic import BaseModel

router = APIRouter()

class GoalCreate(BaseModel):
    name: str
    target: float
    achieved: float = 0
    daysLeft: int = 30
    color: str = "bg-blue-400"

@router.get("/")
def get_goals():
    return {"status": 200, "data": get_all_goals()}

@router.post("/")
def add_goal(goal: GoalCreate):
    new_g = create_goal(goal.dict())
    return {"status": 201, "data": new_g}
