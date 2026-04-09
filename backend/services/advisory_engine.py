from __future__ import annotations


def generate_financial_advice(metrics: dict, budget_snapshot: dict, prediction: dict, expense_split: dict, behavior_profile: dict | None = None) -> dict:
    recommended_savings = round(max(float(metrics.get("totalIncome", 0)) * 0.2, float(metrics.get("netSavings", 0)) * 0.35), 2)
    allocation = {
        "essentials": round(min(55.0, max(float(expense_split.get("fixed_percent", 0)), 35.0)), 2),
        "flexible": round(max(15.0, min(float(expense_split.get("variable_percent", 0)), 35.0)), 2),
        "savings": round(max(10.0, min(100.0, (recommended_savings / max(float(metrics.get("totalIncome", 1)), 1)) * 100)), 2),
    }
    advice: list[str] = []

    if float(prediction.get("confidence_score", 0)) < 0.45:
        advice.append("Prediction confidence is moderate, so keep a larger cash buffer before discretionary spending.")
    if float(metrics.get("savingsRatio", 0)) < 20:
        advice.append("Your savings ratio is low. Increase automated savings contributions before adding new recurring expenses.")
    if float(expense_split.get("fixed_percent", 0)) > 65:
        advice.append("Fixed commitments are dominating your budget. Review subscriptions, EMIs, and utilities first.")
    if float(budget_snapshot["global"].get("usage_percent", 0)) > 80:
        advice.append("Monthly budget utilization is high. Reduce variable spending until the next cycle.")
    if behavior_profile:
        if behavior_profile.get("behavior_profile") == "high fixed burden":
            advice.append("Behavioral profiling shows a high fixed burden. Prioritize renegotiating fixed commitments before lifestyle upgrades.")
        elif behavior_profile.get("behavior_profile") == "high variable spending":
            advice.append("Behavioral profiling shows flexible overspending. Use stricter discretionary controls this cycle.")
    if not advice:
        advice.append("Your current spending pattern is balanced. Continue prioritizing savings and keep discretionary expenses within budget.")

    return {
        "recommended_savings": recommended_savings,
        "budget_allocation": allocation,
        "advice": advice[:4],
        "behavior_profile": behavior_profile.get("behavior_profile", "balanced") if behavior_profile else "balanced",
    }
