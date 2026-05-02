from __future__ import annotations

import argparse
from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.pipeline import Pipeline

from data_processing import build_preprocessor, load_dataset, preprocess_raw_transactions, set_seed, split_dataset
from feature_engineering import engineer_features
from reporting import (
    append_metrics_csv,
    configure_logger,
    generate_research_docx,
    next_model_version,
    save_confusion_matrix_plot,
    save_feature_importance_plot,
    save_model_comparison_plot,
    utc_now_iso,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Train SmartSpend models and generate research artifacts.")
    parser.add_argument("--dataset", default="data/transactions.csv")
    parser.add_argument("--models-dir", default="models")
    parser.add_argument("--results-dir", default="results")
    parser.add_argument("--reports-dir", default="reports")
    parser.add_argument("--test-size", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--run-tag", default="manual")
    return parser.parse_args()


def calc_metrics(y_true, y_pred) -> dict[str, float]:
    from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score

    return {
        "accuracy": accuracy_score(y_true, y_pred),
        "precision": precision_score(y_true, y_pred, zero_division=0),
        "recall": recall_score(y_true, y_pred, zero_division=0),
        "f1_score": f1_score(y_true, y_pred, zero_division=0),
    }


def train_model(name: str, estimator, preprocessor, X_train, y_train, X_test, y_test) -> tuple[Pipeline, dict[str, float]]:
    pipe = Pipeline(steps=[("preprocess", preprocessor), ("model", estimator)])
    pipe.fit(X_train, y_train)
    preds = pipe.predict(X_test)
    metrics = calc_metrics(y_test, preds)
    return pipe, metrics


def main() -> None:
    args = parse_args()

    dataset_path = Path(args.dataset)
    models_dir = Path(args.models_dir)
    results_dir = Path(args.results_dir)
    reports_dir = Path(args.reports_dir)
    results_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)
    logger = configure_logger(results_dir, "smartspend-train")

    set_seed(args.seed)
    logger.info("Starting training | dataset=%s | run_tag=%s", dataset_path, args.run_tag)
    raw_df = load_dataset(dataset_path)
    clean_df = preprocess_raw_transactions(raw_df)
    feat_df = engineer_features(clean_df)

    X = feat_df.drop(columns=["user_id", "target"])
    y = feat_df["target"].astype(int)
    X_train, X_test, y_train, y_test = split_dataset(X, y, test_size=args.test_size, seed=args.seed)
    preprocessor = build_preprocessor(X)

    candidates = {
        "RandomForest": RandomForestClassifier(
            n_estimators=220,
            random_state=args.seed,
            n_jobs=-1,
            class_weight="balanced",
        ),
        "LogisticRegression": LogisticRegression(
            random_state=args.seed,
            max_iter=700,
            class_weight="balanced",
        ),
    }

    trained = {}
    comparison_rows: list[dict[str, object]] = []
    for name, estimator in candidates.items():
        logger.info("Training candidate model=%s", name)
        pipe, metrics = train_model(name, estimator, preprocessor, X_train, y_train, X_test, y_test)
        trained[name] = pipe
        comparison_rows.append({"model_name": name, **metrics})
        logger.info(
            "Metrics | model=%s | accuracy=%.4f precision=%.4f recall=%.4f f1=%.4f",
            name,
            metrics["accuracy"],
            metrics["precision"],
            metrics["recall"],
            metrics["f1_score"],
        )

    comparison_df = pd.DataFrame(comparison_rows).sort_values("f1_score", ascending=False).reset_index(drop=True)
    comparison_df.to_csv(results_dir / "model_comparison.csv", index=False)

    best_model_name = str(comparison_df.iloc[0]["model_name"])
    best_metrics = comparison_df.iloc[0].to_dict()
    second_metrics = comparison_df.iloc[1].to_dict() if len(comparison_df) > 1 else None
    best_reason = (
        f"Highest F1-score ({best_metrics['f1_score']:.4f})"
        if second_metrics is None
        else (
            f"Highest F1-score ({best_metrics['f1_score']:.4f}) vs "
            f"{second_metrics['model_name']} ({second_metrics['f1_score']:.4f})"
        )
    )
    logger.info("Selected best model=%s | reason=%s", best_model_name, best_reason)
    (results_dir / "model_selection.txt").write_text(
        f"Selected model: {best_model_name}\nReason: {best_reason}\n",
        encoding="utf-8",
    )

    version = next_model_version(models_dir)
    model_path = models_dir / f"model_v{version}.pkl"
    best_pipe = trained[best_model_name]

    payload = {
        "model": best_pipe,
        "model_name": best_model_name,
        "version": version,
        "trained_at_utc": utc_now_iso(),
        "metrics": best_metrics,
        "feature_columns": X.columns.tolist(),
        "seed": args.seed,
    }
    joblib.dump(payload, model_path)
    logger.info("Saved model artifact: %s", model_path)

    best_preds = best_pipe.predict(X_test)
    pd.DataFrame({"y_true": y_test.values, "y_pred": best_preds}).to_csv(results_dir / "predictions.csv", index=False)
    class_report = classification_report(y_test, best_preds, zero_division=0)
    (results_dir / "classification_report.txt").write_text(class_report, encoding="utf-8")

    save_confusion_matrix_plot(y_test, best_preds, results_dir / "confusion_matrix.png", f"Confusion Matrix ({best_model_name})")
    save_model_comparison_plot(comparison_df, results_dir / "model_comparison.png")

    model_step = best_pipe.named_steps["model"]
    preproc_step = best_pipe.named_steps["preprocess"]
    feature_names = preproc_step.get_feature_names_out()
    if hasattr(model_step, "feature_importances_"):
        importances = model_step.feature_importances_
    elif hasattr(model_step, "coef_"):
        importances = abs(model_step.coef_[0])
    else:
        importances = [0.0] * len(feature_names)
    save_feature_importance_plot(feature_names, importances, results_dir / "feature_importance.png")

    for _, row in comparison_df.iterrows():
        append_metrics_csv(
            results_dir,
            {
                "timestamp_utc": utc_now_iso(),
                "run_tag": args.run_tag,
                "dataset": str(dataset_path),
                "model_version": version if row["model_name"] == best_model_name else "",
                "selected_best_model": row["model_name"] == best_model_name,
                "reason_for_selection": best_reason if row["model_name"] == best_model_name else "",
                "model_name": row["model_name"],
                "accuracy": row["accuracy"],
                "precision": row["precision"],
                "recall": row["recall"],
                "f1_score": row["f1_score"],
            },
        )

    report_path = generate_research_docx(
        reports_dir=reports_dir,
        results_dir=results_dir,
        comparison_df=comparison_df,
        best_model_name=best_model_name,
        best_reason=best_reason,
    )
    logger.info("Generated research report: %s", report_path)
    logger.info("Training pipeline complete.")


if __name__ == "__main__":
    main()
