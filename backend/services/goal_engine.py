from backend.storage import Storage
from typing import Dict, Any

def get_all_goals() -> list:
    return Storage.get_goals()

def create_goal(goal_data: Dict[str, Any]) -> Dict[str, Any]:
    new_goal = {
        "name": goal_data.get("name"),
        "target": float(goal_data.get("target", 0)),
        "achieved": float(goal_data.get("achieved", 0)),
        "daysLeft": int(goal_data.get("daysLeft", 30)),
        "color": goal_data.get("color", "bg-blue-400")
    }
    return Storage.add_goal(new_goal)
