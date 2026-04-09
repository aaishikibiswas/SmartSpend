from __future__ import annotations


def calculate_networth(metrics: dict, emi_summary: dict) -> dict:
    assets = round(float(metrics.get("totalBalance", 0)) + max(float(metrics.get("netSavings", 0)), 0.0), 2)
    liabilities = round(float(emi_summary.get("remaining_liability", 0)), 2)
    return {
        "assets": assets,
        "liabilities": liabilities,
        "net_worth": round(assets - liabilities, 2),
    }

