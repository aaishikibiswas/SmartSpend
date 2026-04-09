from backend.storage import goals_db
from typing import Dict, Any

def get_all_goals() -> list:
    return goals_db

def create_goal(goal_data: Dict[str, Any]) -> Dict[str, Any]:
    goal_id = max([g["id"] for g in goals_db], default=0) + 1
    new_goal = {
        "id": goal_id,
        "name": goal_data.get("name"),
        "target": float(goal_data.get("target", 0)),
        "achieved": float(goal_data.get("achieved", 0)),
        "daysLeft": int(goal_data.get("daysLeft", 30)),
        "color": goal_data.get("color", "bg-blue-400")
    }
    goals_db.append(new_goal)
    return new_goal
