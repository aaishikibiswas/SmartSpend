from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import tensorflow as tf
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import MinMaxScaler


def regression_metrics(y_true, y_pred):
    y_true_array = np.asarray(y_true, dtype=float)
    y_pred_array = np.asarray(y_pred, dtype=float)
    denominator = np.maximum(np.abs(y_true_array), 1e-6)
    return {
        "rmse": round(float(np.sqrt(mean_squared_error(y_true_array, y_pred_array))), 4),
        "mae": round(float(mean_absolute_error(y_true_array, y_pred_array)), 4),
        "mape": round(float(np.mean(np.abs((y_true_array - y_pred_array) / denominator)) * 100), 4),
        "r2": round(float(r2_score(y_true_array, y_pred_array)), 4),
    }


def build_windows(features: np.ndarray, targets: np.ndarray, window_size: int):
    X = []
    y = []
    for index in range(window_size, len(features)):
        X.append(features[index - window_size:index])
        y.append(targets[index])
    return np.asarray(X, dtype=float), np.asarray(y, dtype=float)


def build_model(window_size: int, feature_count: int):
    model = tf.keras.Sequential(
        [
            tf.keras.layers.Input(shape=(window_size, feature_count)),
            tf.keras.layers.LSTM(32),
            tf.keras.layers.Dense(16, activation="relu"),
            tf.keras.layers.Dense(1),
        ]
    )
    model.compile(optimizer="adam", loss="mse")
    return model


def train_mode(input_path: Path, model_path: Path, metrics_path: Path):
    payload = np.load(input_path, allow_pickle=True)
    train_X = payload["train_X"]
    train_y = payload["train_y"]
    val_X = payload["val_X"]
    val_y = payload["val_y"]
    test_X = payload["test_X"]
    test_y = payload["test_y"]
    scaler_min = payload["scaler_min"]
    scaler_scale = payload["scaler_scale"]
    window_size = int(payload["window_size"][0])
    feature_count = int(payload["feature_count"][0])

    model = build_model(window_size, feature_count)
    model.fit(train_X, train_y, validation_data=(val_X, val_y), epochs=25, batch_size=8, verbose=0)
    model.export(model_path)

    val_pred = model.predict(val_X, verbose=0).reshape(-1)
    test_pred = model.predict(test_X, verbose=0).reshape(-1)
    metrics = {
        "status": "trained",
        "validation": regression_metrics(val_y, val_pred),
        "test": regression_metrics(test_y, test_pred),
        "scaler_min": scaler_min.tolist(),
        "scaler_scale": scaler_scale.tolist(),
        "window_size": window_size,
        "feature_count": feature_count,
        "model_path": str(model_path),
    }
    metrics_path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    print(json.dumps(metrics))


def predict_mode(input_path: Path, model_path: Path):
    payload = np.load(input_path, allow_pickle=True)
    window = payload["window"]
    model = tf.keras.models.load_model(model_path)
    pred = model.predict(window, verbose=0).reshape(-1)[0]
    print(json.dumps({"prediction": round(float(pred), 6)}))


def main():
    mode = sys.argv[1]
    if mode == "train":
        train_mode(Path(sys.argv[2]), Path(sys.argv[3]), Path(sys.argv[4]))
        return
    if mode == "predict":
        predict_mode(Path(sys.argv[2]), Path(sys.argv[3]))
        return
    raise SystemExit(f"Unsupported mode: {mode}")


if __name__ == "__main__":
    main()
