from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.neural_network import MLPRegressor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import MinMaxScaler, StandardScaler
from xgboost import XGBRegressor

from backend.utils.feature_engineering import build_sequence_windows, create_lag_features

Sequential = None
LSTM = None
Dense = None
TENSORFLOW_AVAILABLE = None

_forecast_models: dict[str, object] = {}
_forecast_metadata: dict[str, object] = {}
_forecast_evaluation: dict[str, object] = {}


FEATURE_COLUMNS = [
    "lag1",
    "lag2",
    "lag3",
    "rolling_mean_3",
    "rolling_mean_7",
    "rolling_std_7",
    "trend_3",
    "day_of_week",
    "week_of_year",
    "month",
    "day_of_month",
    "is_weekend",
    "behavior_fixed_ratio",
    "behavior_volatility",
    "behavior_trend",
    "behavior_top_category_share",
]

BEHAVIOR_FEATURES = [
    "behavior_fixed_ratio",
    "behavior_volatility",
    "behavior_trend",
    "behavior_top_category_share",
]
ROLLING_FEATURES = ["rolling_mean_3", "rolling_mean_7", "rolling_std_7"]
CALENDAR_FEATURES = ["day_of_week", "week_of_year", "month", "day_of_month", "is_weekend"]
TREND_FEATURES = ["trend_3"]

ARTIFACTS_DIR = Path(__file__).resolve().parents[1] / "artifacts"
EVALUATION_PATH = ARTIFACTS_DIR / "forecast_evaluation.json"
EXPERIMENT_LOG_PATH = ARTIFACTS_DIR / "forecast_experiments.jsonl"
LSTM_MODEL_PATH = Path(__file__).resolve().parent / "lstm_saved_model"
LSTM_METRICS_PATH = ARTIFACTS_DIR / "lstm_metrics.json"


def _build_model_pipelines() -> dict[str, Pipeline]:
    return {
        "lag_rf": Pipeline(
            [
                ("scaler", StandardScaler()),
                ("regressor", RandomForestRegressor(n_estimators=120, random_state=42, max_depth=6)),
            ]
        ),
        "xgb_trend": Pipeline(
            [
                ("scaler", StandardScaler()),
                (
                    "regressor",
                    XGBRegressor(
                        n_estimators=120,
                        max_depth=4,
                        learning_rate=0.08,
                        subsample=0.9,
                        colsample_bytree=0.9,
                        objective="reg:squarederror",
                        random_state=42,
                    ),
                ),
            ]
        ),
        "sequence_mlp": Pipeline(
            [
                ("scaler", StandardScaler()),
                ("regressor", MLPRegressor(hidden_layer_sizes=(32, 16), activation="relu", max_iter=1500, random_state=42)),
            ]
        ),
    }


def _load_tensorflow_keras():
    global TENSORFLOW_AVAILABLE, Sequential, LSTM, Dense
    if TENSORFLOW_AVAILABLE is not None:
        return TENSORFLOW_AVAILABLE
    try:
        import tensorflow as tf

        Sequential = tf.keras.Sequential
        LSTM = tf.keras.layers.LSTM
        Dense = tf.keras.layers.Dense
        TENSORFLOW_AVAILABLE = True
    except Exception:
        Sequential = None
        LSTM = None
        Dense = None
        TENSORFLOW_AVAILABLE = False
    return TENSORFLOW_AVAILABLE


def _build_lstm_model(window_size: int, feature_count: int):
    if not _load_tensorflow_keras():
        raise RuntimeError("TensorFlow/Keras unavailable")
    model = Sequential(
        [
            LSTM(32, input_shape=(window_size, feature_count)),
            Dense(16, activation="relu"),
            Dense(1),
        ]
    )
    model.compile(optimizer="adam", loss="mse")
    return model


def _regression_metrics(y_true: pd.Series | np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    y_true_array = np.asarray(y_true, dtype=float)
    y_pred_array = np.asarray(y_pred, dtype=float)
    denominator = np.maximum(np.abs(y_true_array), 1e-6)
    return {
        "rmse": round(float(np.sqrt(mean_squared_error(y_true_array, y_pred_array))), 4),
        "mae": round(float(mean_absolute_error(y_true_array, y_pred_array)), 4),
        "mape": round(float(np.mean(np.abs((y_true_array - y_pred_array) / denominator)) * 100), 4),
        "r2": round(float(r2_score(y_true_array, y_pred_array)), 4),
    }


def _safe_time_series_splits(df_features: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame] | None:
    total_rows = len(df_features)
    if total_rows < 12:
        return None

    train_end = max(6, int(total_rows * 0.6))
    val_end = max(train_end + 2, int(total_rows * 0.8))
    if val_end >= total_rows:
        val_end = total_rows - 2
    if train_end >= val_end or val_end >= total_rows:
        return None

    train_df = df_features.iloc[:train_end].copy()
    val_df = df_features.iloc[train_end:val_end].copy()
    test_df = df_features.iloc[val_end:].copy()
    if train_df.empty or val_df.empty or test_df.empty:
        return None
    return train_df, val_df, test_df


def _evaluate_ablation(train_df: pd.DataFrame, test_df: pd.DataFrame, features: list[str]) -> dict[str, float]:
    model = Pipeline(
        [
            ("scaler", StandardScaler()),
            (
                "regressor",
                XGBRegressor(
                    n_estimators=100,
                    max_depth=4,
                    learning_rate=0.08,
                    subsample=0.9,
                    colsample_bytree=0.9,
                    objective="reg:squarederror",
                    random_state=42,
                ),
            ),
        ]
    )
    model.fit(train_df[features], train_df["amount"])
    predictions = model.predict(test_df[features])
    return _regression_metrics(test_df["amount"], predictions)


def _train_lstm(train_df: pd.DataFrame, val_df: pd.DataFrame, test_df: pd.DataFrame, window_size: int = 5):
    if not _load_tensorflow_keras():
        return _train_lstm_subprocess(train_df, val_df, test_df, window_size=window_size)

    scaler = MinMaxScaler()
    scaled_train = scaler.fit_transform(train_df[FEATURE_COLUMNS])
    scaled_val = scaler.transform(val_df[FEATURE_COLUMNS])
    scaled_test = scaler.transform(test_df[FEATURE_COLUMNS])

    train_scaled_df = train_df.copy()
    val_scaled_df = val_df.copy()
    test_scaled_df = test_df.copy()
    train_scaled_df[FEATURE_COLUMNS] = scaled_train
    val_scaled_df[FEATURE_COLUMNS] = scaled_val
    test_scaled_df[FEATURE_COLUMNS] = scaled_test

    X_train, y_train = build_sequence_windows(train_scaled_df, FEATURE_COLUMNS, "amount", window_size=window_size)
    X_val, y_val = build_sequence_windows(pd.concat([train_scaled_df.tail(window_size), val_scaled_df], ignore_index=True), FEATURE_COLUMNS, "amount", window_size=window_size)
    X_test, y_test = build_sequence_windows(pd.concat([val_scaled_df.tail(window_size), test_scaled_df], ignore_index=True), FEATURE_COLUMNS, "amount", window_size=window_size)
    if len(X_train) == 0 or len(X_val) == 0 or len(X_test) == 0:
        return None, {"status": "unavailable", "note": "Not enough sequential samples for LSTM evaluation."}

    model = _build_lstm_model(window_size, len(FEATURE_COLUMNS))
    model.fit(X_train, y_train, validation_data=(X_val, y_val), epochs=25, batch_size=8, verbose=0)
    val_predictions = model.predict(X_val, verbose=0).reshape(-1)
    test_predictions = model.predict(X_test, verbose=0).reshape(-1)
    return {
        "model": model,
        "scaler": scaler,
        "window_size": window_size,
    }, {
        "status": "trained",
        "validation": _regression_metrics(y_val, val_predictions),
        "test": _regression_metrics(y_test, test_predictions),
    }


def _train_lstm_subprocess(train_df: pd.DataFrame, val_df: pd.DataFrame, test_df: pd.DataFrame, window_size: int = 5):
    try:
        scaler = MinMaxScaler()
        train_scaled = scaler.fit_transform(train_df[FEATURE_COLUMNS])
        val_scaled = scaler.transform(val_df[FEATURE_COLUMNS])
        test_scaled = scaler.transform(test_df[FEATURE_COLUMNS])

        train_X, train_y = build_sequence_windows(
            pd.DataFrame(train_scaled, columns=FEATURE_COLUMNS).assign(amount=train_df["amount"].to_numpy()),
            FEATURE_COLUMNS,
            "amount",
            window_size=window_size,
        )
        val_source = np.vstack([train_scaled[-window_size:], val_scaled])
        val_targets = np.concatenate([train_df["amount"].to_numpy()[-window_size:], val_df["amount"].to_numpy()])
        val_X, val_y = build_sequence_windows(
            pd.DataFrame(val_source, columns=FEATURE_COLUMNS).assign(amount=val_targets),
            FEATURE_COLUMNS,
            "amount",
            window_size=window_size,
        )
        test_source = np.vstack([val_scaled[-window_size:], test_scaled])
        test_targets = np.concatenate([val_df["amount"].to_numpy()[-window_size:], test_df["amount"].to_numpy()])
        test_X, test_y = build_sequence_windows(
            pd.DataFrame(test_source, columns=FEATURE_COLUMNS).assign(amount=test_targets),
            FEATURE_COLUMNS,
            "amount",
            window_size=window_size,
        )
        if len(train_X) == 0 or len(val_X) == 0 or len(test_X) == 0:
            return None, {"status": "unavailable", "note": "Not enough sequential samples for LSTM evaluation."}

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "lstm_train_input.npz"
            np.savez(
                input_path,
                train_X=train_X,
                train_y=train_y,
                val_X=val_X,
                val_y=val_y,
                test_X=test_X,
                test_y=test_y,
                scaler_min=scaler.min_,
                scaler_scale=scaler.scale_,
                window_size=np.asarray([window_size]),
                feature_count=np.asarray([len(FEATURE_COLUMNS)]),
            )
            command = [
                sys.executable,
                str(Path(__file__).resolve().parent / "lstm_worker.py"),
                "train",
                str(input_path),
                str(LSTM_MODEL_PATH),
                str(LSTM_METRICS_PATH),
            ]
            completed = subprocess.run(command, capture_output=True, text=True, timeout=1200)
            if completed.returncode != 0:
                return None, {
                    "status": "unavailable",
                    "note": f"LSTM subprocess training failed: {completed.stderr[-300:] if completed.stderr else completed.stdout[-300:]}",
                }
        metrics = json.loads(LSTM_METRICS_PATH.read_text(encoding="utf-8"))
        bundle = {
            "model_path": metrics["model_path"],
            "window_size": metrics["window_size"],
            "scaler_min": np.asarray(metrics["scaler_min"], dtype=float),
            "scaler_scale": np.asarray(metrics["scaler_scale"], dtype=float),
            "subprocess": True,
        }
        return bundle, metrics
    except Exception as exc:
        return None, {"status": "unavailable", "note": f"LSTM subprocess fallback failed: {exc}"}


def _write_experiment_artifacts(report: dict[str, object]) -> None:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    EVALUATION_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    with EXPERIMENT_LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(report) + "\n")


def _format_model_comparison(evaluation_models: dict[str, object]) -> dict[str, object]:
    comparison = {}
    best_model = None
    best_rmse = None
    for name, details in evaluation_models.items():
        if not isinstance(details, dict):
            continue
        test_metrics = details.get("test", {})
        if not isinstance(test_metrics, dict) or not test_metrics:
            comparison[name] = details
            continue
        comparison[name.upper() if name != "xgb_trend" else "XGB"] = test_metrics
        rmse = test_metrics.get("rmse")
        if isinstance(rmse, (int, float)) and (best_rmse is None or rmse < best_rmse):
            best_rmse = float(rmse)
            best_model = name.upper() if name != "xgb_trend" else "XGB"
    return {
        "table": comparison,
        "best_model": best_model,
        "selection_metric": "rmse",
    }


def train_regression_model(transactions_df: pd.DataFrame):
    global _forecast_models, _forecast_metadata, _forecast_evaluation
    _forecast_models = {}
    _forecast_metadata = {}
    _forecast_evaluation = {}

    expense_df = transactions_df[transactions_df["amount"] < 0].copy() if not transactions_df.empty else pd.DataFrame()
    if expense_df.empty:
        return False

    expense_df["amount"] = expense_df["amount"].abs()
    df_features = create_lag_features(expense_df, "amount")
    if len(df_features) < 8:
        return False

    X = df_features[FEATURE_COLUMNS]
    y = df_features["amount"]
    split_frames = _safe_time_series_splits(df_features)
    weights = {"lag_rf": 0.28, "xgb_trend": 0.28, "sequence_mlp": 0.18, "lstm": 0.26}

    evaluation_models: dict[str, dict[str, dict[str, float] | str]] = {}
    lstm_bundle = None
    if split_frames:
        train_df, val_df, test_df = split_frames
        val_predictions: dict[str, np.ndarray] = {}
        test_predictions: dict[str, np.ndarray] = {}

        for name, model in _build_model_pipelines().items():
            model.fit(train_df[FEATURE_COLUMNS], train_df["amount"])
            val_pred = np.asarray(model.predict(val_df[FEATURE_COLUMNS]), dtype=float)
            test_pred = np.asarray(model.predict(test_df[FEATURE_COLUMNS]), dtype=float)
            val_predictions[name] = val_pred
            test_predictions[name] = test_pred
            evaluation_models[name] = {
                "validation": _regression_metrics(val_df["amount"], val_pred),
                "test": _regression_metrics(test_df["amount"], test_pred),
            }

        lstm_bundle, lstm_metrics = _train_lstm(train_df, val_df, test_df)
        evaluation_models["lstm"] = lstm_metrics

        if lstm_bundle and lstm_metrics.get("status") == "trained":
            if lstm_bundle.get("subprocess"):
                evaluation_models["lstm"] = lstm_metrics
            else:
                combined_train = pd.concat([train_df, val_df], ignore_index=True)
                combined_scaled = combined_train.copy()
                combined_scaled[FEATURE_COLUMNS] = lstm_bundle["scaler"].transform(combined_train[FEATURE_COLUMNS])
                test_scaled = test_df.copy()
                test_scaled[FEATURE_COLUMNS] = lstm_bundle["scaler"].transform(test_df[FEATURE_COLUMNS])
                _, _ = build_sequence_windows(combined_scaled, FEATURE_COLUMNS, "amount", window_size=lstm_bundle["window_size"])
                X_test_seq, _y_test_seq = build_sequence_windows(pd.concat([combined_scaled.tail(lstm_bundle["window_size"]), test_scaled], ignore_index=True), FEATURE_COLUMNS, "amount", window_size=lstm_bundle["window_size"])
                if len(X_test_seq):
                    test_predictions["lstm"] = lstm_bundle["model"].predict(X_test_seq, verbose=0).reshape(-1)
                    val_seq_source = pd.concat([train_df.tail(lstm_bundle["window_size"]), val_df], ignore_index=True)
                    val_seq_scaled = val_seq_source.copy()
                    val_seq_scaled[FEATURE_COLUMNS] = lstm_bundle["scaler"].transform(val_seq_source[FEATURE_COLUMNS])
                    X_val_seq, _y_val_seq = build_sequence_windows(val_seq_scaled, FEATURE_COLUMNS, "amount", window_size=lstm_bundle["window_size"])
                    if len(X_val_seq):
                        val_predictions["lstm"] = lstm_bundle["model"].predict(X_val_seq, verbose=0).reshape(-1)

        ensemble_names = [name for name in ("lag_rf", "xgb_trend", "sequence_mlp", "lstm") if name in test_predictions and name in val_predictions]
        if ensemble_names:
            val_common_len = min(len(val_predictions[name]) for name in ensemble_names)
            test_common_len = min(len(test_predictions[name]) for name in ensemble_names)
            weight_sum = sum(weights.get(name, 0.1) for name in ensemble_names)
            ensemble_val = sum(val_predictions[name][-val_common_len:] * (weights.get(name, 0.1) / weight_sum) for name in ensemble_names)
            ensemble_test = sum(test_predictions[name][-test_common_len:] * (weights.get(name, 0.1) / weight_sum) for name in ensemble_names)
        else:
            ensemble_val = np.asarray([])
            ensemble_test = np.asarray([])

        comparison = _format_model_comparison(evaluation_models)
        _forecast_evaluation = {
            "data_split": {
                "strategy": "time_series",
                "train_rows": len(train_df),
                "validation_rows": len(val_df),
                "test_rows": len(test_df),
            },
            "models": evaluation_models,
            "ensemble": {
                "weights": weights,
                "validation": _regression_metrics(val_df["amount"].tail(len(ensemble_val)) if len(ensemble_val) else val_df["amount"], ensemble_val) if len(ensemble_val) else {},
                "test": _regression_metrics(test_df["amount"].tail(len(ensemble_test)) if len(ensemble_test) else test_df["amount"], ensemble_test) if len(ensemble_test) else {},
            },
            "ablation": {
                "full_features": _evaluate_ablation(train_df, test_df, FEATURE_COLUMNS),
                "without_behavioral_features": _evaluate_ablation(train_df, test_df, [feature for feature in FEATURE_COLUMNS if feature not in BEHAVIOR_FEATURES]),
                "without_rolling": _evaluate_ablation(train_df, test_df, [feature for feature in FEATURE_COLUMNS if feature not in ROLLING_FEATURES]),
                "without_calendar": _evaluate_ablation(train_df, test_df, [feature for feature in FEATURE_COLUMNS if feature not in CALENDAR_FEATURES]),
                "lags_only": _evaluate_ablation(train_df, test_df, ["lag1", "lag2", "lag3"]),
                "without_trend": _evaluate_ablation(train_df, test_df, [feature for feature in FEATURE_COLUMNS if feature not in TREND_FEATURES]),
            },
            "deep_learning": {
                "tensorflow_available": bool(_load_tensorflow_keras()),
                "lstm_status": evaluation_models.get("lstm", {}).get("status", "unknown") if isinstance(evaluation_models.get("lstm"), dict) else "unknown",
            },
            "comparison": comparison,
        }
    else:
        _forecast_evaluation = {
            "data_split": {
                "strategy": "time_series",
                "train_rows": len(df_features),
                "validation_rows": 0,
                "test_rows": 0,
            },
            "models": {},
            "ensemble": {},
            "ablation": {},
            "deep_learning": {
                "tensorflow_available": bool(_load_tensorflow_keras()),
                "lstm_status": "insufficient_data",
            },
            "comparison": {
                "table": {},
                "best_model": None,
                "selection_metric": "rmse",
            },
            "note": "Insufficient data for full train/validation/test reporting. Production model still trained on available history.",
        }

    final_models = _build_model_pipelines()
    for model in final_models.values():
        model.fit(X, y)

    _forecast_models = final_models
    if _load_tensorflow_keras() and len(df_features) > 10:
        scaled_df = df_features.copy()
        lstm_scaler = MinMaxScaler()
        scaled_df[FEATURE_COLUMNS] = lstm_scaler.fit_transform(df_features[FEATURE_COLUMNS])
        X_seq, y_seq = build_sequence_windows(scaled_df, FEATURE_COLUMNS, "amount", window_size=5)
        if len(X_seq):
            final_lstm = _build_lstm_model(5, len(FEATURE_COLUMNS))
            final_lstm.fit(X_seq, y_seq, epochs=25, batch_size=8, verbose=0)
            try:
                final_lstm.save(LSTM_MODEL_PATH, include_optimizer=False)
            except Exception:
                pass
            _forecast_models["lstm"] = {
                "model": final_lstm,
                "scaler": lstm_scaler,
                "window_size": 5,
                "model_path": str(LSTM_MODEL_PATH),
            }

    _forecast_metadata = {
        "feature_columns": FEATURE_COLUMNS,
        "training_rows": len(df_features),
        "latest_features": df_features.tail(1).to_dict(orient="records")[0],
        "evaluation_available": bool(_forecast_evaluation),
        "tensorflow_available": bool(_load_tensorflow_keras()),
    }
    report = {
        "task": "expense_forecasting",
        "model_family": "ensemble_regression_with_optional_lstm",
        "features": FEATURE_COLUMNS,
        "training_rows": len(df_features),
        "evaluation": _forecast_evaluation,
        "comparison": _forecast_evaluation.get("comparison", {}),
    }
    _write_experiment_artifacts(report)
    return True


def get_trained_model():
    return _forecast_models


def get_model_metadata():
    return _forecast_metadata


def get_forecast_evaluation() -> dict[str, object]:
    return _forecast_evaluation
