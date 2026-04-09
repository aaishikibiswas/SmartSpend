from __future__ import annotations

from backend.models.train import FEATURE_COLUMNS, get_forecast_evaluation
from backend.services.anomaly_engine import get_anomaly_research_summary
from backend.services.behavior_engine import build_behavior_profile
from backend.services.categorizer import get_categorizer_evaluation
from backend.services.explainability import SHAP_AVAILABLE
from backend.storage import Storage


def get_research_report() -> dict:
    transactions = Storage.get_transactions()
    forecast_evaluation = get_forecast_evaluation()
    categorizer_evaluation = get_categorizer_evaluation()
    anomaly_evaluation = get_anomaly_research_summary(transactions)
    behavior = build_behavior_profile(transactions)

    return {
        "model_inventory": {
            "forecasting": [
                "RandomForestRegressor",
                "XGBRegressor",
                "MLPRegressor",
                "LSTM",
                "Prophet",
            ],
            "categorization": [
                "TF-IDF Vectorizer",
                "XGBClassifier",
            ],
            "anomaly_detection": [
                "IsolationForest",
            ],
        },
        "feature_engineering": {
            "forecast_features": FEATURE_COLUMNS,
            "categorization_context": ["amount_abs", "token_length", "transaction_month", "income_signal"],
            "behavioral_features": ["fixed_ratio", "variable_ratio", "spending_volatility", "category_frequency", "spending_trend", "top_category_share"],
        },
        "evaluation": {
            "forecasting": forecast_evaluation,
            "categorization": categorizer_evaluation,
            "anomaly_detection": anomaly_evaluation,
        },
        "behavioral_modeling": behavior,
        "limitations": [
            "SHAP explanations are available only if the shap package is installed; otherwise XGBoost contribution scores are used as the explainability backend.",
            "The LSTM path is enabled only when TensorFlow/Keras is available in the runtime.",
            "Supervised fraud benchmarking is not available because there is no labeled fraud dataset in the current runtime.",
        ],
        "research_readiness": {
            "has_time_series_split": bool(forecast_evaluation.get("data_split")),
            "has_regression_metrics": bool(forecast_evaluation.get("ensemble")),
            "has_classification_metrics": bool(categorizer_evaluation.get("test")),
            "has_ablation": bool(forecast_evaluation.get("ablation")),
            "has_experiment_logging": True,
            "shap_available": SHAP_AVAILABLE,
            "lstm_enabled": bool(forecast_evaluation.get("deep_learning", {}).get("tensorflow_available")),
        },
    }
