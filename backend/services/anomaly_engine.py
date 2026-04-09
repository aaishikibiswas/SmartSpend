from __future__ import annotations

import pandas as pd
from sklearn.ensemble import IsolationForest

from backend.utils.feature_engineering import add_transaction_context_features


def _personalized_threshold(expenses: pd.DataFrame) -> float:
    if expenses.empty:
        return 0.15
    daily_spread = float(expenses["amount_abs"].std()) if len(expenses) > 1 else 0.0
    avg_amount = float(expenses["amount_abs"].mean()) if len(expenses) else 0.0
    volatility_ratio = daily_spread / max(avg_amount, 1.0)
    if volatility_ratio > 1.1:
        return 0.2
    if volatility_ratio < 0.45:
        return 0.1
    return 0.15


def score_transaction_anomalies(transactions_df: pd.DataFrame) -> list[dict]:
    if transactions_df.empty:
        return []

    features_df = add_transaction_context_features(transactions_df)
    expenses = features_df[features_df["amount"] < 0].copy() if "amount" in features_df.columns else pd.DataFrame()
    if expenses.empty or len(expenses) < 5:
        return []

    contamination = _personalized_threshold(expenses)
    model_features = expenses[["amount_abs", "day_of_week", "month", "merchant_frequency", "category_frequency"]]
    detector = IsolationForest(contamination=contamination, random_state=42)
    detector.fit(model_features)
    anomaly_flags = detector.predict(model_features)
    anomaly_scores = detector.decision_function(model_features)

    amount_mean = float(expenses["amount_abs"].mean()) if len(expenses) else 0.0
    amount_std = float(expenses["amount_abs"].std()) if len(expenses) > 1 else 0.0

    flagged: list[dict] = []
    for (_, row), flag, score in zip(expenses.iterrows(), anomaly_flags, anomaly_scores):
        if flag != -1:
            continue
        personalized_risk = "High" if (row["amount_abs"] > amount_mean + (2 * amount_std)) or score < -0.12 else "Medium"
        flagged.append(
            {
                "merchant": row["merchant"],
                "category": row["category"],
                "date": str(row["date"])[:10],
                "amount": round(float(row["amount_abs"]), 2),
                "anomaly_score": round(float(-score), 4),
                "risk_flag": personalized_risk,
                "personalized": True,
            }
        )

    flagged.sort(key=lambda item: item["anomaly_score"], reverse=True)
    return flagged


def latest_anomaly_summary(transactions_df: pd.DataFrame) -> dict:
    anomalies = score_transaction_anomalies(transactions_df)
    return {
        "count": len(anomalies),
        "top": anomalies[:3],
    }


def get_anomaly_research_summary(transactions_df: pd.DataFrame) -> dict:
    anomalies = score_transaction_anomalies(transactions_df)
    expenses = transactions_df[transactions_df["amount"] < 0].copy() if not transactions_df.empty else pd.DataFrame()
    scored = [float(item["anomaly_score"]) for item in anomalies]
    total_expenses = int(len(expenses))
    return {
        "model": "IsolationForest",
        "evaluation_mode": "unsupervised_proxy_with_personalized_thresholding",
        "total_expense_transactions": total_expenses,
        "flagged_count": len(anomalies),
        "flagged_ratio": round((len(anomalies) / total_expenses) * 100, 4) if total_expenses else 0.0,
        "average_flagged_score": round(sum(scored) / len(scored), 4) if scored else 0.0,
        "note": "Personalized thresholds are derived from the user's own spending volatility and amount distribution.",
    }
