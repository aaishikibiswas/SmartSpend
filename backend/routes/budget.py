from fastapi import APIRouter
from pydantic import BaseModel, Field

from backend.services.alert_engine import generate_alerts, get_all_alerts
from backend.services.budget_engine import (
    add_or_update_category_budget,
    build_budget_feedback,
    get_budget_snapshot,
    get_category_budget_summary,
    get_global_budget_summary,
    remove_category_budget,
    set_global_budget,
)
from backend.storage import Storage

router = APIRouter()


class GlobalBudgetPayload(BaseModel):
    monthly_budget: float = Field(ge=0)
    auto_distribute: bool = False


class CategoryBudgetPayload(BaseModel):
    name: str
    amount: float = Field(ge=0)
    frequency: str = "Monthly"


def _refresh_budget_dependent_systems():
    Storage.reset_alerts()
    transactions = Storage.get_transactions()
    generate_alerts(transactions)
    return transactions


@router.get("/global")
def get_global_budget():
    transactions = Storage.get_transactions()
    return {
        "status": 200,
        "data": get_global_budget_summary(transactions),
    }


@router.post("/global")
def update_global_budget(payload: GlobalBudgetPayload):
    transactions = Storage.get_transactions()
    summary = set_global_budget(payload.monthly_budget, payload.auto_distribute, transactions)
    transactions = _refresh_budget_dependent_systems()

    return {
        "status": 200,
        "data": {
            "global": summary,
            "categories": get_category_budget_summary(transactions),
            "feedback": build_budget_feedback(transactions),
            "alerts": get_all_alerts(),
        },
        "message": "Global budget updated successfully.",
    }


@router.get("/category")
def get_category_budget():
    transactions = Storage.get_transactions()
    return {
        "status": 200,
        "data": get_category_budget_summary(transactions),
    }


@router.post("/category")
def upsert_category_budget(payload: CategoryBudgetPayload):
    transactions = Storage.get_transactions()
    category = add_or_update_category_budget(payload.name, payload.amount, payload.frequency, transactions)
    transactions = _refresh_budget_dependent_systems()

    return {
        "status": 200,
        "data": {
            "category": category,
            "categories": get_category_budget_summary(transactions),
            "feedback": build_budget_feedback(transactions),
            "alerts": get_all_alerts(),
        },
        "message": "Category budget saved successfully.",
    }


@router.delete("/category/{name}")
def delete_category_budget(name: str):
    transactions = Storage.get_transactions()
    categories = remove_category_budget(name, transactions)
    transactions = _refresh_budget_dependent_systems()

    return {
        "status": 200,
        "data": {
            "categories": categories,
            "feedback": build_budget_feedback(transactions),
            "alerts": get_all_alerts(),
        },
        "message": "Category budget removed successfully.",
    }


@router.get("/snapshot")
def get_budget_snapshot_route():
    transactions = Storage.get_transactions()
    return {
        "status": 200,
        "data": get_budget_snapshot(transactions),
    }
