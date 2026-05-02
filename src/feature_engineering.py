from __future__ import annotations

import pandas as pd


def engineer_features(data: pd.DataFrame) -> pd.DataFrame:
    """User-level financial behavior features for classification."""
    df = data.copy()
    df["month"] = df["date"].dt.to_period("M").astype(str)
    df["is_weekend"] = df["date"].dt.dayofweek.isin([5, 6]).astype(int)

    amount_mean = df["amount"].mean()
    amount_std = df["amount"].std() + 1e-6
    df["anomaly_indicator"] = (((df["amount"] - amount_mean) / amount_std).abs() > 2).astype(int)

    monthly_spend = (
        df[df["type"] == "debit"]
        .groupby(["user_id", "month"])["amount"]
        .sum()
        .reset_index(name="monthly_spend")
        .groupby("user_id")["monthly_spend"]
        .mean()
        .rename("monthly_spend_user")
    )

    category_frequency = (
        df.groupby(["user_id", "category"])
        .size()
        .reset_index(name="cnt")
        .groupby("user_id")["cnt"]
        .max()
        .rename("top_category_frequency")
    )

    dominant_category = (
        df.groupby(["user_id", "category"])
        .size()
        .reset_index(name="cnt")
        .sort_values(["user_id", "cnt"], ascending=[True, False])
        .drop_duplicates("user_id")[["user_id", "category"]]
        .rename(columns={"category": "dominant_category"})
    )

    agg = (
        df.groupby("user_id")
        .agg(
            total_transactions=("amount", "count"),
            avg_amount=("amount", "mean"),
            total_amount=("amount", "sum"),
            weekend_ratio=("is_weekend", "mean"),
            anomaly_count=("anomaly_indicator", "sum"),
        )
        .reset_index()
    )

    income = df[df["type"] == "credit"].groupby("user_id")["amount"].sum().rename("total_income")
    expense = df[df["type"] == "debit"].groupby("user_id")["amount"].sum().rename("total_expense")

    features = agg.merge(income, on="user_id", how="left").merge(expense, on="user_id", how="left")
    features = features.merge(monthly_spend, on="user_id", how="left")
    features = features.merge(category_frequency, on="user_id", how="left")
    features = features.merge(dominant_category, on="user_id", how="left")

    features["total_income"] = features["total_income"].fillna(0)
    features["total_expense"] = features["total_expense"].fillna(0)
    features["monthly_spend_user"] = features["monthly_spend_user"].fillna(features["monthly_spend_user"].median())
    features["top_category_frequency"] = features["top_category_frequency"].fillna(features["top_category_frequency"].median())
    features["dominant_category"] = features["dominant_category"].fillna("Unknown")
    features["expense_income_ratio"] = features["total_expense"] / (features["total_income"] + 1e-6)

    if "target" in df.columns:
        target_user = (
            df.groupby("user_id")["target"]
            .agg(lambda s: s.mode().iloc[0] if not s.mode().empty else s.iloc[0])
            .rename("target")
        )
        features = features.merge(target_user, on="user_id", how="left")
    else:
        # Synthetic risk label fallback for demos/research if dataset is unlabeled.
        features["target"] = (
            (features["expense_income_ratio"] > 0.9)
            | (features["anomaly_count"] >= 3)
            | (features["weekend_ratio"] > 0.45)
        ).astype(int)

    features["target"] = features["target"].fillna(0).astype(int)
    return features

