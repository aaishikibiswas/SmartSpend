from __future__ import annotations

import argparse
from pathlib import Path

import joblib
import pandas as pd
from sklearn.metrics import classification_report, confusion_matrix

from data_processing import load_dataset, preprocess_raw_transactions, set_seed, split_dataset
from feature_engineering import engineer_features
from reporting import append_metrics_csv, configure_logger, latest_model_path, save_confusion_matrix_plot, utc_now_iso


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Evaluate latest SmartSpend model.")
    parser.add_argument("--dataset", default="data/transactions.csv")
    parser.add_argument("--models-dir", default="models")
    parser.add_argument("--results-dir", default="results")
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--run-tag", default="eval")
    return parser.parse_args()


def calc_metrics(y_true, y_pred) -> dict[str, float]:
    from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

    return {
        "accuracy": accuracy_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall": recall_score(y_true, y_pred, zero_division=0),
        "f1_score": f1_score(y_true, y_pred, zero_division=0),
    }


def main() -> None:
    args = parse_args()
    set_seed(args.seed)
    dataset_path = Path(args.dataset)
    models_dir = Path(args.models_dir)
    results_dir = Path(args.results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)
    logger = configure_logger(results_dir, "smartspend-evaluate")

    model_path = latest_model_path(models_dir)
    if model_path is None:
        raise FileNotFoundError(f"No versioned model found in: {models_dir}")

    payload = joblib.load(model_path)
    model = payload["model"]
    model_name = payload.get("model_name", "unknown")
    model_version = payload.get("version", "")

    raw_df = load_dataset(dataset_path)
    clean_df = preprocess_raw_transactions(raw_df)
    feat_df = engineer_features(clean_df)

    X = feat_df.drop(columns=["user_id", "target"])
    y = feat_df["target"].astype(int)
    _, X_test, _, y_test = split_dataset(X, y, test_size=args.test_size, seed=args.seed)

    y_pred = model.predict(X_test)
    metrics = calc_metrics(y_test, y_pred)

    report_text = classification_report(y_test, y_pred, zero_division=0)
    (results_dir / "classification_report.txt").write_text(report_text, encoding="utf-8")
    pd.DataFrame(confusion_matrix(y_test, y_pred)).to_csv(results_dir / "confusion_matrix.csv", index=False)
    save_confusion_matrix_plot(y_test, y_pred, results_dir / "confusion_matrix.png", f"Confusion Matrix ({model_name})")

    append_metrics_csv(
        results_dir,
        {
            "timestamp_utc": utc_now_iso(),
            "run_tag": args.run_tag,
            "dataset": str(dataset_path),
            "model_version": model_version,
            "selected_best_model": True,
            "reason_for_selection": "Evaluation run",
            "model_name": model_name,
            **metrics,
        },
    )

    logger.info(
        "Evaluation complete | model=%s v%s | accuracy=%.4f precision=%.4f recall=%.4f f1=%.4f",
        model_name,
        model_version,
        metrics["accuracy"],
        metrics["precision"],
        metrics["recall"],
        metrics["f1_score"],
    )


if __name__ == "__main__":
    main()

