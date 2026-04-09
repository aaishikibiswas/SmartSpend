from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
from prophet import Prophet

from backend.models.train import FEATURE_COLUMNS, get_model_metadata, get_trained_model
from backend.services.behavior_engine import build_behavior_profile
from backend.services.budget_engine import get_global_budget_summary
from backend.services.emi_engine import summarize_emis
from backend.services.explainability import explain_ensemble
from backend.services.subscription_engine import get_all_subscriptions
from backend.storage import Storage
from backend.utils.feature_engineering import build_sequence_windows, create_lag_features


def build_daily_expense_series(transactions_df: pd.DataFrame) -> pd.DataFrame:
    expenses = transactions_df[transactions_df["amount"] < 0].copy()
    if expenses.empty:
        return pd.DataFrame(columns=["date", "amount"])
    expenses["amount"] = expenses["amount"].abs()
    return expenses.groupby("date")["amount"].sum().reset_index().sort_values("date")


def _elevate_risk(base_risk: str, usage_percent: float, predicted_expense: float, remaining_budget: float, recurring_load: float = 0.0, behavior_profile: str = "balanced") -> str:
    risk_levels = ["Low", "Medium", "High"]
    idx = risk_levels.index(base_risk) if base_risk in risk_levels else 0
    if usage_percent >= 100 or predicted_expense > max(remaining_budget, 0):
        idx = max(idx, 2)
    elif usage_percent >= 80 or recurring_load > max(remaining_budget, 1):
        idx = max(idx, 1)
    if behavior_profile in {"high fixed burden", "high variable spending"}:
        idx = min(2, max(idx, 1))
    return risk_levels[idx]


def _build_explanation(features: dict, ensemble_outputs: dict[str, float], predicted_expense: float, explainability_bundle: dict | None = None) -> list[dict]:
    factors = {
        "lag1": abs(float(features.get("lag1", 0))),
        "lag2": abs(float(features.get("lag2", 0))),
        "rolling_mean_7": abs(float(features.get("rolling_mean_7", 0))),
        "trend_3": abs(float(features.get("trend_3", 0))),
        "behavior_fixed_ratio": abs(float(features.get("behavior_fixed_ratio", 0))),
        "behavior_volatility": abs(float(features.get("behavior_volatility", 0))),
    }
    if explainability_bundle:
        for model_info in explainability_bundle.get("models", {}).values():
            for item in model_info.get("contributions", [])[:3]:
                factors[item["feature"]] = max(factors.get(item["feature"], 0.0), abs(float(item.get("impact", 0))))
    ranked = sorted(factors.items(), key=lambda item: item[1], reverse=True)[:4]
    explanations = [
        {
            "feature": name,
            "impact_score": round(value, 2),
            "note": f"{name} contributed to the predicted expense level.",
        }
        for name, value in ranked
    ]
    explanations.append(
        {
            "feature": "ensemble",
            "impact_score": round(float(np.std(list(ensemble_outputs.values()))) if ensemble_outputs else 0, 2),
            "note": f"Ensemble consensus shaped the final forecast of Rs{round(predicted_expense, 2)}.",
        }
    )
    return explanations


def _fallback_prediction(daily_expenses: pd.DataFrame, budget_summary: dict, recurring_load: float, behavior_profile: dict) -> dict:
    if daily_expenses.empty:
        return {
            "predicted_expense": 0.0,
            "risk_level": "Low",
            "budget_usage_percent": 0.0,
            "recurring_load": round(recurring_load, 2),
            "confidence_score": 0.0,
            "trend_direction": "stable",
            "ensemble_breakdown": {},
            "model_contributions": {},
            "behavior_profile": behavior_profile.get("behavior_profile", "balanced"),
            "shap_explanations": {"shap_available": False, "models": {}},
            "explanations": [],
        }

    values = daily_expenses["amount"].tolist()
    recent = values[-3:]
    while len(recent) < 3:
        recent.insert(0, recent[0] if recent else 0.0)

    weighted = (recent[-1] * 0.5) + (recent[-2] * 0.3) + (recent[-3] * 0.2)
    baseline = float(np.mean(values))
    risk = "High" if weighted > baseline * 1.35 else "Medium" if weighted > baseline * 1.1 else "Low"
    adjusted_risk = _elevate_risk(risk, float(budget_summary["usage_percent"]), float(weighted), float(budget_summary["remaining_amount"]), recurring_load, str(behavior_profile.get("behavior_profile", "balanced")))
    trend = "upward" if recent[-1] >= recent[0] else "downward"
    return {
        "predicted_expense": round(float(weighted), 2),
        "risk_level": adjusted_risk,
        "budget_usage_percent": round(float(budget_summary["usage_percent"]), 2),
        "recurring_load": round(recurring_load, 2),
        "confidence_score": 0.42,
        "trend_direction": trend,
        "ensemble_breakdown": {"heuristic": round(float(weighted), 2)},
        "model_contributions": {"heuristic": 1.0},
        "behavior_profile": behavior_profile.get("behavior_profile", "balanced"),
        "shap_explanations": {"shap_available": False, "models": {}},
        "explanations": [
            {"feature": "lag_recency", "impact_score": round(abs(recent[-1]), 2), "note": "Recent daily spend heavily influenced the fallback forecast."}
        ],
    }


def _prophet_next_point(daily_expenses: pd.DataFrame) -> float:
    if len(daily_expenses) < 5:
        return 0.0
    prophet_df = daily_expenses.rename(columns={"date": "ds", "amount": "y"})
    prophet_df["ds"] = pd.to_datetime(prophet_df["ds"])
    model = Prophet(daily_seasonality=True, yearly_seasonality=False, weekly_seasonality=True)
    model.fit(prophet_df)
    future = model.make_future_dataframe(periods=1)
    forecast = model.predict(future)
    return max(0.0, float(forecast.tail(1)["yhat"].iloc[0]))


def _predict_lstm(lstm_bundle: dict, feature_frame: pd.DataFrame) -> float | None:
    try:
        window_size = int(lstm_bundle["window_size"])
        if len(feature_frame) <= window_size:
            return None
        if lstm_bundle.get("subprocess"):
            scaled = feature_frame.copy()
            scaled_values = feature_frame[FEATURE_COLUMNS].to_numpy(dtype=float)
            scaled[FEATURE_COLUMNS] = (scaled_values * np.asarray(lstm_bundle["scaler_scale"], dtype=float)) + np.asarray(lstm_bundle["scaler_min"], dtype=float)
            X_windows, _ = build_sequence_windows(scaled, FEATURE_COLUMNS, "amount", window_size=window_size)
            if len(X_windows) == 0:
                return None
            with tempfile.TemporaryDirectory() as tmpdir:
                input_path = Path(tmpdir) / "lstm_predict_input.npz"
                np.savez(input_path, window=X_windows[-1:].reshape(1, window_size, len(FEATURE_COLUMNS)))
                command = [
                    sys.executable,
                    str(Path(__file__).resolve().parent / "lstm_worker.py"),
                    "predict",
                    str(input_path),
                    str(lstm_bundle["model_path"]),
                ]
                completed = subprocess.run(command, capture_output=True, text=True, timeout=180)
                if completed.returncode != 0:
                    return None
                output = json.loads(completed.stdout.strip().splitlines()[-1])
                return max(0.0, float(output["prediction"]))
        scaled = feature_frame.copy()
        scaled[FEATURE_COLUMNS] = lstm_bundle["scaler"].transform(feature_frame[FEATURE_COLUMNS])
        X_windows, _ = build_sequence_windows(scaled, FEATURE_COLUMNS, "amount", window_size=window_size)
        if len(X_windows) == 0:
            return None
        prediction = lstm_bundle["model"].predict(X_windows[-1:].reshape(1, window_size, len(FEATURE_COLUMNS)), verbose=0).reshape(-1)[0]
        return max(0.0, float(prediction))
    except Exception:
        return None


def predict_next_expense(daily_expenses: pd.DataFrame) -> dict:
    models = get_trained_model()
    metadata = get_model_metadata()
    budget_summary = get_global_budget_summary()
    transactions = Storage.get_transactions()
    behavior_profile = build_behavior_profile(transactions)
    recurring_load = float(summarize_emis(transactions)["monthly_load"]) + sum(float(item["monthly_cost"]) for item in get_all_subscriptions(transactions))

    if daily_expenses.empty or not models or len(daily_expenses) < 8:
        return _fallback_prediction(daily_expenses, budget_summary, recurring_load, behavior_profile)

    feature_frame = create_lag_features(daily_expenses.assign(amount=daily_expenses["amount"]), "amount")
    if feature_frame.empty:
        return _fallback_prediction(daily_expenses, budget_summary, recurring_load, behavior_profile)

    latest_features = feature_frame.tail(1)[FEATURE_COLUMNS]
    latest_row = feature_frame.tail(1).to_dict(orient="records")[0]

    ensemble_outputs: dict[str, float] = {}
    weights = {"lag_rf": 0.28, "xgb_trend": 0.28, "sequence_mlp": 0.18, "lstm": 0.16, "prophet": 0.10}

    for name, model in models.items():
        if name == "lstm":
            prediction = _predict_lstm(model, feature_frame)
            if prediction is not None:
                ensemble_outputs[name] = prediction
            continue
        try:
            ensemble_outputs[name] = max(0.0, float(model.predict(latest_features)[0]))
        except Exception:
            continue

    prophet_value = _prophet_next_point(daily_expenses)
    if prophet_value > 0:
        ensemble_outputs["prophet"] = prophet_value

    if not ensemble_outputs:
        return _fallback_prediction(daily_expenses, budget_summary, recurring_load, behavior_profile)

    normalized_weight_sum = sum(weights.get(name, 0.1) for name in ensemble_outputs)
    model_contributions = {name: round(weights.get(name, 0.1) / normalized_weight_sum, 4) for name in ensemble_outputs}
    predicted_expense = sum(value * model_contributions[name] for name, value in ensemble_outputs.items())

    baseline = float(daily_expenses["amount"].mean())
    risk = "High" if predicted_expense > baseline * 1.35 else "Medium" if predicted_expense > baseline * 1.1 else "Low"
    adjusted_risk = _elevate_risk(
        risk,
        float(budget_summary["usage_percent"]),
        float(predicted_expense),
        float(budget_summary["remaining_amount"]),
        recurring_load,
        str(behavior_profile.get("behavior_profile", "balanced")),
    )
    values = daily_expenses["amount"].tolist()
    trend = "upward" if values[-1] >= values[max(0, len(values) - 4)] else "downward"
    spread = float(np.std(list(ensemble_outputs.values()))) if len(ensemble_outputs) > 1 else 0.0
    confidence = max(0.15, min(0.98, 1 - (spread / max(predicted_expense, 1))))
    explainability_bundle = explain_ensemble({name: model for name, model in models.items() if name != "lstm"}, latest_features, FEATURE_COLUMNS)

    return {
        "predicted_expense": round(float(predicted_expense), 2),
        "risk_level": adjusted_risk,
        "budget_usage_percent": round(float(budget_summary["usage_percent"]), 2),
        "recurring_load": round(recurring_load, 2),
        "confidence_score": round(confidence, 3),
        "trend_direction": trend,
        "ensemble_breakdown": {name: round(value, 2) for name, value in ensemble_outputs.items()},
        "model_contributions": model_contributions,
        "behavior_profile": behavior_profile.get("behavior_profile", "balanced"),
        "shap_explanations": explainability_bundle,
        "explanations": _build_explanation(metadata.get("latest_features", latest_row), ensemble_outputs, predicted_expense, explainability_bundle),
    }


def generate_prophet_forecast(transactions_df: pd.DataFrame, days: int = 15) -> dict:
    daily_expenses = build_daily_expense_series(transactions_df)

    if len(daily_expenses) < 5:
        base = daily_expenses["amount"].tolist()[-3:] if not daily_expenses.empty else [0.0]
        while len(base) < 3:
            base.insert(0, base[0] if base else 0.0)
        weighted = (base[-1] * 0.5) + (base[-2] * 0.3) + (base[-3] * 0.2)
        series = [round(float(max(weighted * (1 + (0.02 * i)), 0.0)), 2) for i in range(days)]
        peak_idx = series.index(max(series)) if series else 0
        return {"peakAlert": {"day": f"Day {peak_idx + 1}", "amount": series[peak_idx] if series else 0.0}, "series": series}

    prophet_df = daily_expenses.rename(columns={"date": "ds", "amount": "y"})
    prophet_df["ds"] = pd.to_datetime(prophet_df["ds"])
    model = Prophet(daily_seasonality=True, yearly_seasonality=False, weekly_seasonality=True)
    model.fit(prophet_df)
    future = model.make_future_dataframe(periods=days)
    forecast = model.predict(future)
    future_forecast = [max(0, round(float(y), 2)) for y in forecast.tail(days)["yhat"].values]
    peak_idx = future_forecast.index(max(future_forecast))
    return {"peakAlert": {"day": f"Day {peak_idx + 1}", "amount": max(future_forecast)}, "series": future_forecast}
