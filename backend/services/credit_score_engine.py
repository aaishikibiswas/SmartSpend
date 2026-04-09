from __future__ import annotations

from typing import Any


def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def get_credit_category(score: int) -> str:
    if score >= 750:
        return "Excellent"
    if score >= 650:
        return "Good"
    if score >= 550:
        return "Fair"
    return "Risky"


def build_credit_suggestions(
    savings_ratio: float,
    expense_volatility: float,
    anomaly_count: int,
    expense_income_ratio: float,
) -> list[str]:
    suggestions: list[str] = []

    if savings_ratio < 20:
        suggestions.append("Increase monthly savings contributions to strengthen your financial buffer.")
    if expense_volatility > 5000:
        suggestions.append("Reduce irregular spending spikes to improve behavioral stability.")
    if anomaly_count > 1:
        suggestions.append("Review unusual transactions and eliminate suspicious or avoidable outliers.")
    if expense_income_ratio > 0.75:
        suggestions.append("Lower expense load relative to income to improve affordability confidence.")

    if not suggestions:
        suggestions.append("Maintain your current discipline to preserve a strong behavioral credit profile.")

    return suggestions


def calculate_credit_score(features: dict[str, Any]) -> dict[str, Any]:
    income = float(features.get("income", 0) or 0)
    total_expense = float(features.get("total_expense", 0) or 0)
    savings_ratio = float(features.get("savings_ratio", 0) or 0)
    expense_volatility = float(features.get("expense_volatility", 0) or 0)
    anomaly_count = int(features.get("anomaly_count", 0) or 0)

    expense_income_ratio = (total_expense / income) if income > 0 else 1.0

    savings_contribution = clamp((savings_ratio / 35) * 100, -20, 100)
    volatility_contribution = clamp(((6000 - expense_volatility) / 6000) * 80, -80, 80)
    anomaly_contribution = clamp(-(anomaly_count * 23), -70, 0)
    expense_ratio_contribution = clamp(((0.55 - expense_income_ratio) / 0.55) * 100, -100, 80)

    raw_score = 600 + savings_contribution + volatility_contribution + anomaly_contribution + expense_ratio_contribution
    final_score = int(round(clamp(raw_score, 300, 900)))
    category = get_credit_category(final_score)

    if expense_volatility <= 1800:
        spending_stability = "High"
    elif expense_volatility <= 4200:
        spending_stability = "Medium"
    else:
        spending_stability = "Low"

    if savings_ratio >= 30:
        savings_band = "Strong"
    elif savings_ratio >= 15:
        savings_band = "Moderate"
    else:
        savings_band = "Weak"

    if anomaly_count == 0 and expense_income_ratio < 0.65:
        risk_level = "Low"
    elif anomaly_count <= 2 and expense_income_ratio < 0.85:
        risk_level = "Medium"
    else:
        risk_level = "High"

    contributions = {
        "savings_ratio": round(float(savings_contribution), 2),
        "volatility": round(float(volatility_contribution), 2),
        "anomalies": round(float(anomaly_contribution), 2),
        "expense_income_ratio": round(float(expense_ratio_contribution), 2),
    }

    return {
        "score": final_score,
        "category": category,
        "range": {"min": 300, "max": 900},
        "indicators": {
            "spending_stability": spending_stability,
            "savings_ratio": savings_band,
            "risk_level": risk_level,
        },
        "feature_contributions": contributions,
        "explainability": {
            "top_positive_driver": max(contributions, key=contributions.get),
            "top_negative_driver": min(contributions, key=contributions.get),
        },
        "suggestions": build_credit_suggestions(
            savings_ratio=savings_ratio,
            expense_volatility=expense_volatility,
            anomaly_count=anomaly_count,
            expense_income_ratio=expense_income_ratio,
        ),
        "disclaimer": "This is a behavioral credit estimate, not an official bank score.",
    }
