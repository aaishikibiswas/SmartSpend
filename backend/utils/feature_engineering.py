from __future__ import annotations

import numpy as np
import pandas as pd


def create_lag_features(df: pd.DataFrame, target_col: str = "amount") -> pd.DataFrame:
    """
    Create forecasting-ready features from daily spend history.
    Compatible with tree models, sequence learners, and Prophet side channels.
    """
    if df.empty or target_col not in df.columns:
        return pd.DataFrame()

    working = df.copy()
    working["date"] = pd.to_datetime(working["date"], errors="coerce")
    working = working.dropna(subset=["date"])
    if working.empty:
        return pd.DataFrame()

    daily = working.groupby("date")[target_col].sum().reset_index().sort_values("date")
    if daily.empty:
        return pd.DataFrame()

    daily["lag1"] = daily[target_col].shift(1).fillna(0)
    daily["lag2"] = daily[target_col].shift(2).fillna(0)
    daily["lag3"] = daily[target_col].shift(3).fillna(0)
    daily["rolling_mean_3"] = daily[target_col].rolling(3, min_periods=1).mean()
    daily["rolling_mean_7"] = daily[target_col].rolling(7, min_periods=1).mean()
    daily["rolling_std_7"] = daily[target_col].rolling(7, min_periods=1).std().fillna(0)
    daily["trend_3"] = daily[target_col].diff().rolling(3, min_periods=1).mean().fillna(0)
    daily["day_of_week"] = daily["date"].dt.dayofweek
    daily["week_of_year"] = daily["date"].dt.isocalendar().week.astype(int)
    daily["month"] = daily["date"].dt.month
    daily["day_of_month"] = daily["date"].dt.day
    daily["is_weekend"] = daily["day_of_week"].isin([5, 6]).astype(int)

    behavior = compute_behavior_features(working)
    daily["behavior_fixed_ratio"] = float(behavior["fixed_ratio"])
    daily["behavior_volatility"] = float(behavior["spending_volatility"])
    daily["behavior_trend"] = float(behavior["spending_trend"])
    daily["behavior_top_category_share"] = float(behavior["top_category_share"])
    return daily


def add_transaction_context_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build tabular features for classification/anomaly models from transaction-level data.
    """
    if df.empty:
        return pd.DataFrame()

    working = df.copy()
    working["date"] = pd.to_datetime(working["date"], errors="coerce")
    working["merchant"] = working["merchant"].astype(str)
    working["category"] = working["category"].astype(str)
    working["amount_abs"] = working["amount"].abs()
    working["day_of_week"] = working["date"].dt.dayofweek.fillna(0).astype(int)
    working["month"] = working["date"].dt.month.fillna(0).astype(int)
    working["hour_bucket"] = 12
    merchant_counts = working["merchant"].value_counts().to_dict()
    category_counts = working["category"].value_counts().to_dict()
    working["merchant_frequency"] = working["merchant"].map(merchant_counts).fillna(1).astype(float)
    working["category_frequency"] = working["category"].map(category_counts).fillna(1).astype(float)
    return working


def compute_behavior_features(df: pd.DataFrame) -> dict:
    if df.empty:
        return {
            "fixed_ratio": 0.0,
            "variable_ratio": 0.0,
            "spending_volatility": 0.0,
            "category_frequency": {},
            "spending_trend": 0.0,
            "top_category_share": 0.0,
            "behavior_profile": "balanced",
        }

    working = df.copy()
    if "date" in working.columns:
        working["date"] = pd.to_datetime(working["date"], errors="coerce")
    expenses = working[working["amount"] < 0].copy() if "amount" in working.columns else pd.DataFrame()
    if expenses.empty:
        return {
            "fixed_ratio": 0.0,
            "variable_ratio": 0.0,
            "spending_volatility": 0.0,
            "category_frequency": {},
            "spending_trend": 0.0,
            "top_category_share": 0.0,
            "behavior_profile": "balanced",
        }

    fixed_categories = {"housing", "emi", "subscription", "bills", "utilities", "rent"}
    expenses["amount_abs"] = expenses["amount"].abs()
    expenses["category_normalized"] = expenses["category"].astype(str).str.strip().str.lower()
    expenses["expense_class"] = np.where(expenses["category_normalized"].isin(fixed_categories), "fixed", "variable")

    fixed_total = float(expenses.loc[expenses["expense_class"] == "fixed", "amount_abs"].sum())
    variable_total = float(expenses.loc[expenses["expense_class"] == "variable", "amount_abs"].sum())
    total = max(fixed_total + variable_total, 1e-6)

    daily = expenses.groupby("date")["amount_abs"].sum().reset_index().sort_values("date")
    volatility = float(daily["amount_abs"].std()) if len(daily) > 1 else 0.0
    trend = float(daily["amount_abs"].diff().rolling(3, min_periods=1).mean().iloc[-1]) if len(daily) > 1 else 0.0

    category_totals = expenses.groupby("category")["amount_abs"].sum().sort_values(ascending=False)
    top_share = float(category_totals.iloc[0] / total) if len(category_totals) else 0.0
    category_frequency = {str(key): int(value) for key, value in expenses["category"].value_counts().to_dict().items()}

    if fixed_total / total > 0.7:
        profile = "high fixed burden"
    elif variable_total / total > 0.7:
        profile = "high variable spending"
    else:
        profile = "balanced"

    return {
        "fixed_ratio": round((fixed_total / total) * 100, 4),
        "variable_ratio": round((variable_total / total) * 100, 4),
        "spending_volatility": round(volatility, 4),
        "category_frequency": category_frequency,
        "spending_trend": round(trend, 4),
        "top_category_share": round(top_share * 100, 4),
        "behavior_profile": profile,
    }


def build_sequence_windows(df_features: pd.DataFrame, feature_columns: list[str], target_column: str = "amount", window_size: int = 5):
    if df_features.empty or len(df_features) <= window_size:
        return np.asarray([]), np.asarray([])

    values = df_features[feature_columns].to_numpy(dtype=float)
    targets = df_features[target_column].to_numpy(dtype=float)
    X_windows = []
    y_windows = []
    for index in range(window_size, len(df_features)):
        X_windows.append(values[index - window_size:index])
        y_windows.append(targets[index])
    return np.asarray(X_windows, dtype=float), np.asarray(y_windows, dtype=float)
