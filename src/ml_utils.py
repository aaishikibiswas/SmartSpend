from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, StandardScaler


MODEL_PATTERN = re.compile(r"model_v(\d+)\.pkl$")


@dataclass(frozen=True)
class Paths:
    dataset: Path
    models_dir: Path
    results_dir: Path


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def configure_logger(results_dir: Path, log_name: str) -> logging.Logger:
    results_dir.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger(log_name)
    logger.setLevel(logging.INFO)
    logger.handlers.clear()

    formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

    file_handler = logging.FileHandler(results_dir / "train.log", encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    return logger


def load_transactions_csv(dataset_path: Path) -> pd.DataFrame:
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset not found: {dataset_path}")
    df = pd.read_csv(dataset_path)
    return df


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    required_cols = {"user_id", "date", "amount", "category", "type"}
    missing = sorted(required_cols - set(df.columns))
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    data = df.copy()
    data["date"] = pd.to_datetime(data["date"], errors="coerce")
    data = data.dropna(subset=["date"]).copy()
    data["category"] = data["category"].fillna("Unknown")
    data["type"] = data["type"].fillna("debit").str.lower()
    data["amount"] = pd.to_numeric(data["amount"], errors="coerce")
    data["amount"] = data["amount"].fillna(data["amount"].median())

    data["month"] = data["date"].dt.to_period("M").astype(str)
    data["is_weekend"] = data["date"].dt.dayofweek.isin([5, 6]).astype(int)

    amount_mean = data["amount"].mean()
    amount_std = data["amount"].std() + 1e-6
    data["anomaly_indicator"] = (((data["amount"] - amount_mean) / amount_std).abs() > 2).astype(int)

    monthly_spend = (
        data[data["type"] == "debit"]
        .groupby(["user_id", "month"])["amount"]
        .sum()
        .reset_index(name="monthly_spend")
        .groupby("user_id")["monthly_spend"]
        .mean()
        .rename("monthly_spend_user")
    )

    category_frequency = (
        data.groupby(["user_id", "category"])
        .size()
        .reset_index(name="cnt")
        .groupby("user_id")["cnt"]
        .max()
        .rename("top_category_frequency")
    )

    agg = (
        data.groupby("user_id")
        .agg(
            total_transactions=("amount", "count"),
            avg_amount=("amount", "mean"),
            total_amount=("amount", "sum"),
            weekend_ratio=("is_weekend", "mean"),
            anomaly_count=("anomaly_indicator", "sum"),
        )
        .reset_index()
    )

    income = data[data["type"] == "credit"].groupby("user_id")["amount"].sum().rename("total_income")
    expense = data[data["type"] == "debit"].groupby("user_id")["amount"].sum().rename("total_expense")

    dominant_category = (
        data.groupby(["user_id", "category"])
        .size()
        .reset_index(name="cnt")
        .sort_values(["user_id", "cnt"], ascending=[True, False])
        .drop_duplicates("user_id")[["user_id", "category"]]
        .rename(columns={"category": "dominant_category"})
    )

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

    if "target" in data.columns:
        target_user = (
            data.groupby("user_id")["target"]
            .agg(lambda s: s.mode().iloc[0] if not s.mode().empty else s.iloc[0])
            .rename("target")
        )
        features = features.merge(target_user, on="user_id", how="left")
    else:
        features["target"] = (
            (features["expense_income_ratio"] > 0.9)
            | (features["anomaly_count"] >= 3)
            | (features["weekend_ratio"] > 0.45)
        ).astype(int)

    features["target"] = features["target"].fillna(0).astype(int)
    return features


def build_preprocessor(X: pd.DataFrame) -> ColumnTransformer:
    numeric_cols = X.select_dtypes(include=["number"]).columns.tolist()
    categorical_cols = X.select_dtypes(exclude=["number"]).columns.tolist()

    numeric_pipeline = Pipeline(
        steps=[
            ("to_writable", FunctionTransformer(to_writable, validate=False)),
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    categorical_pipeline = Pipeline(
        steps=[
            ("to_writable", FunctionTransformer(to_writable, validate=False)),
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OneHotEncoder(handle_unknown="ignore")),
        ]
    )

    return ColumnTransformer(
        transformers=[
            ("num", numeric_pipeline, numeric_cols),
            ("cat", categorical_pipeline, categorical_cols),
        ]
    )


def to_writable(values):
    # Some environments pass readonly views to sklearn transformers.
    # Enforce a writable copy to keep training stable across CI/notebooks/local.
    return np.asarray(values).copy()


def build_models(seed: int) -> Dict[str, object]:
    return {
        "RandomForest": RandomForestClassifier(
            n_estimators=200,
            random_state=seed,
            n_jobs=-1,
            class_weight="balanced",
        ),
        "LogisticRegression": LogisticRegression(
            max_iter=600,
            random_state=seed,
            class_weight="balanced",
        ),
    }


def calc_metrics(y_true, y_pred) -> Dict[str, float]:
    return {
        "accuracy": accuracy_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall": recall_score(y_true, y_pred, zero_division=0),
        "f1_score": f1_score(y_true, y_pred, zero_division=0),
    }


def next_model_version(models_dir: Path) -> int:
    models_dir.mkdir(parents=True, exist_ok=True)
    versions = []
    for model_path in models_dir.glob("model_v*.pkl"):
        match = MODEL_PATTERN.search(model_path.name)
        if match:
            versions.append(int(match.group(1)))
    return (max(versions) + 1) if versions else 1


def latest_model_path(models_dir: Path) -> Path | None:
    models = []
    for model_path in models_dir.glob("model_v*.pkl"):
        match = MODEL_PATTERN.search(model_path.name)
        if match:
            models.append((int(match.group(1)), model_path))
    if not models:
        return None
    return sorted(models, key=lambda x: x[0])[-1][1]


def append_metrics_csv(results_dir: Path, row: Dict[str, object]) -> Path:
    results_dir.mkdir(parents=True, exist_ok=True)
    metrics_path = results_dir / "metrics.csv"
    row_df = pd.DataFrame([row])
    if metrics_path.exists():
        existing = pd.read_csv(metrics_path)
        all_rows = pd.concat([existing, row_df], ignore_index=True)
        all_rows.to_csv(metrics_path, index=False)
    else:
        row_df.to_csv(metrics_path, index=False)
    return metrics_path


def build_pipeline(preprocessor: ColumnTransformer, estimator) -> Pipeline:
    return Pipeline(
        steps=[
            ("preprocess", preprocessor),
            ("model", estimator),
        ]
    )
