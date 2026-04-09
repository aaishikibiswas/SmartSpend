from __future__ import annotations


def build_priorities(metrics: dict, budget_snapshot: dict, subscriptions: list[dict], emi_summary: dict, cashflow: dict) -> list[dict]:
    actions: list[dict] = []

    if float(emi_summary.get("monthly_load", 0)) > 0:
        actions.append(
            {
                "level": "High",
                "title": "Pay EMI Before Lifestyle Spend",
                "message": f"Your fixed EMI load is Rs. {round(float(emi_summary['monthly_load']), 2)} this month. Keep that funded first.",
            }
        )

    if cashflow.get("upcoming_payments"):
        next_payment = cashflow["upcoming_payments"][0]
        actions.append(
            {
                "level": "High",
                "title": f"Prepare For {next_payment['type']}",
                "message": f"{next_payment['name']} is due on {next_payment['date']} for Rs. {round(float(next_payment['amount']), 2)}.",
            }
        )

    if float(budget_snapshot["global"]["usage_percent"]) >= 80:
        actions.append(
            {
                "level": "Medium",
                "title": "Protect Remaining Budget",
                "message": f"Only Rs. {round(float(budget_snapshot['global']['remaining_amount']), 2)} remains in your monthly budget.",
            }
        )

    if subscriptions:
        subscriptions = sorted(subscriptions, key=lambda item: item["monthly_cost"], reverse=True)
        actions.append(
            {
                "level": "Medium",
                "title": "Review Subscriptions",
                "message": f"{subscriptions[0]['name']} is your largest recurring subscription at Rs. {round(float(subscriptions[0]['monthly_cost']), 2)} per month.",
            }
        )

    if float(metrics.get("netSavings", 0)) > 0:
        actions.append(
            {
                "level": "Healthy",
                "title": "Move Leftover To Savings",
                "message": f"You still have positive savings of Rs. {round(float(metrics['netSavings']), 2)}. Keep discretionary spend last.",
            }
        )

    return actions[:4]
