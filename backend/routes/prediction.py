from fastapi import APIRouter
from pydantic import BaseModel

from backend.models.predict import build_daily_expense_series, generate_prophet_forecast, predict_next_expense
from backend.models.train import get_forecast_evaluation, train_regression_model
from backend.storage import Storage

router = APIRouter()


class PredictionRequest(BaseModel):
    timelineDays: int = 15


@router.post("/")
def get_prediction(payload: PredictionRequest):
    df = Storage.get_transactions()
    days = max(1, min(payload.timelineDays, 60))
    forecast_data = generate_prophet_forecast(df, days=days)
    daily_expenses = build_daily_expense_series(df)
    next_expense = predict_next_expense(daily_expenses)

    return {
        "status": 200,
        "data": {
            "forecast": forecast_data,
            "next_expense_prediction": next_expense,
        },
    }


@router.post("/train")
def train_prediction_models():
    df = Storage.get_transactions()
    trained = train_regression_model(df)
    return {
        "status": 200,
        "data": {
            "trained": bool(trained),
            "evaluation": get_forecast_evaluation(),
        },
    }
