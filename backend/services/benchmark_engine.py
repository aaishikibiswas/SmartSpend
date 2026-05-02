from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd


ARTIFACTS_DIR = Path(__file__).resolve().parents[1] / "artifacts"
BENCHMARK_DATASET_PATH = ARTIFACTS_DIR / "benchmark_transactions.csv"


PROFILE_LIBRARY = [
    {
        "name": "balanced_saver",
        "income": 82000,
        "rent": 18000,
        "utilities": 4200,
        "subscription_total": 1400,
        "food_mean": 520,
        "transport_mean": 280,
        "shopping_mean": 700,
        "shopping_probability": 0.12,
    },
    {
        "name": "high_variable_spend",
        "income": 76000,
        "rent": 16000,
        "utilities": 3900,
        "subscription_total": 1800,
        "food_mean": 850,
        "transport_mean": 420,
        "shopping_mean": 1500,
        "shopping_probability": 0.22,
    },
    {
        "name": "fixed_burden",
        "income": 90000,
        "rent": 26000,
        "utilities": 5200,
        "subscription_total": 1100,
        "food_mean": 480,
        "transport_mean": 260,
        "shopping_mean": 550,
        "shopping_probability": 0.08,
    },
    {
        "name": "subscription_heavy",
        "income": 68000,
        "rent": 15000,
        "utilities": 3500,
        "subscription_total": 3200,
        "food_mean": 600,
        "transport_mean": 300,
        "shopping_mean": 850,
        "shopping_probability": 0.15,
    },
]


def _pick_date_anchor(transactions_df: pd.DataFrame, days: int) -> datetime:
    if not transactions_df.empty and "date" in transactions_df.columns:
        parsed = pd.to_datetime(transactions_df["date"], errors="coerce").dropna()
        if not parsed.empty:
            return parsed.min().to_pydatetime() - timedelta(days=max(days // 3, 45))
    return datetime.utcnow() - timedelta(days=days)


def _append_transaction(rows: list[dict], date_value: datetime, merchant: str, category: str, amount: float) -> None:
    rows.append(
        {
            "date": date_value.strftime("%Y-%m-%d"),
            "merchant": merchant,
            "category": category,
            "amount": round(float(amount), 2),
            "type": "credit" if amount > 0 else "debit",
            "language": "en",
        }
    )


def generate_benchmark_transactions(transactions_df: pd.DataFrame, days: int = 180) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    rows: list[dict] = []
    anchor = _pick_date_anchor(transactions_df, days)

    for profile_index, profile in enumerate(PROFILE_LIBRARY):
        profile_offset = profile_index * (days // 3)
        for day_index in range(days):
            current_date = anchor + timedelta(days=profile_offset + day_index)

            if current_date.day == 1:
                _append_transaction(rows, current_date, "Salary Credit", "Income", profile["income"])

            if current_date.day == 3:
                _append_transaction(rows, current_date, "Home Rent", "Housing", -profile["rent"])

            if current_date.day == 6:
                _append_transaction(rows, current_date, "Electricity Bill", "Bills", -profile["utilities"] * 0.62)
                _append_transaction(rows, current_date, "Internet Bill", "Bills", -profile["utilities"] * 0.38)

            if current_date.day == 8:
                _append_transaction(rows, current_date, "Netflix Subscription", "Entertainment", -profile["subscription_total"] * 0.35)
                _append_transaction(rows, current_date, "Spotify Premium", "Entertainment", -profile["subscription_total"] * 0.20)
                _append_transaction(rows, current_date, "Prime Membership", "Entertainment", -profile["subscription_total"] * 0.45)

            if current_date.weekday() in {0, 2, 4, 5}:
                food_amount = max(120, rng.normal(profile["food_mean"], profile["food_mean"] * 0.18))
                _append_transaction(rows, current_date, "Swiggy", "Food", -food_amount)

            if current_date.weekday() in {1, 3, 5}:
                transport_amount = max(80, rng.normal(profile["transport_mean"], profile["transport_mean"] * 0.25))
                merchant = "Uber" if current_date.weekday() != 5 else "Fuel Station"
                _append_transaction(rows, current_date, merchant, "Transport", -transport_amount)

            if rng.random() < profile["shopping_probability"]:
                shopping_amount = max(250, rng.normal(profile["shopping_mean"], profile["shopping_mean"] * 0.35))
                merchant = "Amazon" if rng.random() < 0.55 else "Flipkart"
                _append_transaction(rows, current_date, merchant, "Shopping", -shopping_amount)

            if current_date.weekday() == 6 and rng.random() < 0.55:
                leisure_amount = max(150, rng.normal(450, 120))
                _append_transaction(rows, current_date, "Movie Night", "Entertainment", -leisure_amount)

            if rng.random() < 0.06:
                health_amount = max(180, rng.normal(950, 250))
                _append_transaction(rows, current_date, "Apollo Pharmacy", "Healthcare", -health_amount)

            if rng.random() < 0.03:
                refund_amount = max(120, rng.normal(650, 180))
                _append_transaction(rows, current_date, "Refund Credit", "Income", refund_amount)

    benchmark_df = pd.DataFrame(rows).sort_values("date").reset_index(drop=True)
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    benchmark_df.to_csv(BENCHMARK_DATASET_PATH, index=False)
    return benchmark_df


def get_benchmark_dataset_summary(transactions_df: pd.DataFrame) -> dict:
    benchmark_df = generate_benchmark_transactions(transactions_df)
    return {
        "rows": int(len(benchmark_df)),
        "profiles": [profile["name"] for profile in PROFILE_LIBRARY],
        "date_range": {
            "start": str(benchmark_df["date"].min()) if not benchmark_df.empty else None,
            "end": str(benchmark_df["date"].max()) if not benchmark_df.empty else None,
        },
        "categories": sorted(benchmark_df["category"].astype(str).unique().tolist()) if not benchmark_df.empty else [],
        "artifact_path": str(BENCHMARK_DATASET_PATH),
    }
