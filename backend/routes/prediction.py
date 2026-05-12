from fastapi import APIRouter
from pydantic import BaseModel
import asyncio
from backend.models.predict import build_daily_expense_series, generate_prophet_forecast, predict_next_expense
from backend.models.train import get_forecast_evaluation, train_regression_model
from backend.storage import Storage

router = APIRouter()


class PredictionRequest(BaseModel):
    timelineDays: int = 15


@router.post("/")
async def get_prediction(payload: PredictionRequest):
    df = await asyncio.to_thread(Storage.get_transactions)
    days = max(1, min(payload.timelineDays, 60))
    
    # Run heavy ML in parallel threads
    daily_expenses = await asyncio.to_thread(build_daily_expense_series, df)
    forecast_data, next_expense = await asyncio.gather(
        asyncio.to_thread(generate_prophet_forecast, df, days=days),
        asyncio.to_thread(predict_next_expense, daily_expenses, include_prophet=False)
    )

    return {
        "status": 200,
        "data": {
            "forecast": forecast_data,
            "next_expense_prediction": next_expense,
        },
    }


@router.post("/train")
async def train_prediction_models():
    df = await asyncio.to_thread(Storage.get_transactions)
    trained = await asyncio.to_thread(train_regression_model, df)
    return {
        "status": 200,
        "data": {
            "trained": bool(trained),
            "evaluation": get_forecast_evaluation(),
        },
    }
