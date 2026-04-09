from __future__ import annotations

import pandas as pd

from backend.utils.feature_engineering import compute_behavior_features


def build_behavior_profile(transactions_df: pd.DataFrame) -> dict:
    features = compute_behavior_features(transactions_df)
    return {
        "fixed_ratio": float(features.get("fixed_ratio", 0.0)),
        "variable_ratio": float(features.get("variable_ratio", 0.0)),
        "spending_volatility": float(features.get("spending_volatility", 0.0)),
        "category_frequency": features.get("category_frequency", {}),
        "spending_trend": float(features.get("spending_trend", 0.0)),
        "top_category_share": float(features.get("top_category_share", 0.0)),
        "behavior_profile": str(features.get("behavior_profile", "balanced")),
    }
