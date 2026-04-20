from __future__ import annotations

import json
from pathlib import Path

import joblib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import GridSearchCV
from sklearn.model_selection import StratifiedKFold
from sklearn.model_selection import cross_val_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.svm import SVC

try:
    from xgboost import XGBClassifier
    XGBOOST_AVAILABLE = True
except Exception:
    XGBOOST_AVAILABLE = False


ROOT_DIR = Path(__file__).resolve().parent
DATA_PATH = ROOT_DIR / "sample.csv"
MODEL_PATH = ROOT_DIR / "finset_model.pkl"
ARTIFACTS_DIR = ROOT_DIR / "artifacts"
ARTIFACTS_DIR.mkdir(exist_ok=True)


def infer_category(description: str) -> str:
    text = str(description).lower()
    if any(token in text for token in ["salary", "refund", "cashback", "credit"]):
        return "Income"
    if any(token in text for token in ["zomato", "swiggy", "foodpanda", "food"]):
        return "Food"
    if any(token in text for token in ["ola", "uber", "petrol", "bus", "train"]):
        return "Transport"
    if any(token in text for token in ["flipkart", "amazon", "movie"]):
        return "Shopping"
    if any(token in text for token in ["electricity", "bill", "recharge", "phone", "jio"]):
        return "Bills"
    if "atm" in text:
        return "Cash"
    return "Other"


def load_and_prepare_dataset(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    print("=" * 72)
    print("STEP 1: LOADING DATASET")
    print("=" * 72)
    print(f"Dataset path       : {csv_path}")
    print(f"Rows x Columns     : {df.shape[0]} x {df.shape[1]}")
    print(f"Columns detected   : {list(df.columns)}")
    print()

    df = df.replace("-", np.nan)

    df["Date"] = pd.to_datetime(df["Date"], format="%d-%m-%Y", errors="coerce")
    for col in ["Debit", "Credit", "Balance"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["Description"] = df["Description"].fillna("Unknown")
    df["Category"] = df["Description"].apply(infer_category)
    df["TransactionType"] = np.where(df["Credit"].fillna(0) > 0, "credit", "debit")
    df["Amount"] = np.where(
        df["TransactionType"] == "credit",
        df["Credit"].fillna(0),
        df["Debit"].fillna(0),
    )

    df["DayOfWeek"] = df["Date"].dt.day_name().fillna("Unknown")
    df["Month"] = df["Date"].dt.month_name().fillna("Unknown")
    df["Day"] = df["Date"].dt.day.fillna(0)
    df["IsWeekend"] = df["DayOfWeek"].isin(["Saturday", "Sunday"]).astype(int)
    df["SavingsRatio"] = np.where(
        df["Credit"].fillna(0) > 0,
        (df["Credit"].fillna(0) - df["Debit"].fillna(0)) / df["Credit"].fillna(1),
        0,
    )
    df["ExpenseToBalanceRatio"] = df["Debit"].fillna(0) / df["Balance"].replace(0, np.nan)
    df["ExpenseToBalanceRatio"] = df["ExpenseToBalanceRatio"].replace([np.inf, -np.inf], np.nan)

    debit_mask = df["TransactionType"] == "debit"
    debit_amounts = df.loc[debit_mask, "Amount"]
    high_spend_threshold = debit_amounts.quantile(0.75) if not debit_amounts.empty else 0
    low_balance_threshold = df["Balance"].quantile(0.30)

    discretionary_categories = {"Food", "Shopping", "Transport", "Cash", "Other"}
    df["BehaviorRisk"] = np.where(
        debit_mask
        & (
            (df["Amount"] >= high_spend_threshold)
            | (df["Balance"] <= low_balance_threshold)
            | (
                df["Category"].isin(discretionary_categories)
                & (df["Amount"] >= debit_amounts.median())
            )
        ),
        1,
        0,
    )

    print("=" * 72)
    print("STEP 2: PREPROCESSING SUMMARY")
    print("=" * 72)
    print("Missing values after cleaning:")
    print(df.isna().sum().to_string())
    print()
    print("Target distribution (BehaviorRisk):")
    print(df["BehaviorRisk"].value_counts().sort_index().to_string())
    print()
    return df


def build_preprocessor(categorical_features: list[str], numerical_features: list[str]) -> ColumnTransformer:
    categorical_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OneHotEncoder(handle_unknown="ignore")),
        ]
    )

    numerical_transformer = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )

    return ColumnTransformer(
        transformers=[
            ("categorical", categorical_transformer, categorical_features),
            ("numerical", numerical_transformer, numerical_features),
        ]
    )


def evaluate_model(name: str, model: Pipeline, x_test: pd.DataFrame, y_test: pd.Series) -> dict:
    y_pred = model.predict(x_test)
    report_dict = classification_report(y_test, y_pred, zero_division=0, output_dict=True)
    metrics = {
        "accuracy": accuracy_score(y_test, y_pred),
        "precision": precision_score(y_test, y_pred, zero_division=0),
        "recall": recall_score(y_test, y_pred, zero_division=0),
        "f1_score": f1_score(y_test, y_pred, zero_division=0),
        "confusion_matrix": confusion_matrix(y_test, y_pred).tolist(),
        "classification_report": classification_report(y_test, y_pred, zero_division=0),
        "classification_report_dict": report_dict,
    }

    print("=" * 72)
    print(f"MODEL EVALUATION: {name}")
    print("=" * 72)
    print(f"Accuracy         : {metrics['accuracy']:.4f}")
    print(f"Precision        : {metrics['precision']:.4f}")
    print(f"Recall           : {metrics['recall']:.4f}")
    print(f"F1-score         : {metrics['f1_score']:.4f}")
    print("Confusion Matrix :")
    print(np.array(metrics["confusion_matrix"]))
    print()
    print("Classification Report:")
    print(metrics["classification_report"])
    return metrics


def tune_model(
    name: str,
    pipeline: Pipeline,
    param_grid: dict,
    x_train: pd.DataFrame,
    y_train: pd.Series,
) -> tuple[Pipeline, dict]:
    print("=" * 72)
    print(f"HYPERPARAMETER TUNING: {name}")
    print("=" * 72)
    search = GridSearchCV(
        estimator=pipeline,
        param_grid=param_grid,
        cv=4,
        scoring="accuracy",
        n_jobs=-1,
        refit=True,
    )
    search.fit(x_train, y_train)
    print(f"Best CV Accuracy             : {search.best_score_:.4f}")
    print(f"Best Parameters              : {search.best_params_}")
    print()
    tuning_result = {
        "best_cv_accuracy": float(search.best_score_),
        "best_params": search.best_params_,
    }
    return search.best_estimator_, tuning_result


def compute_cross_validation_metrics(
    model: Pipeline,
    x_train: pd.DataFrame,
    y_train: pd.Series,
) -> dict:
    cv = StratifiedKFold(n_splits=4, shuffle=True, random_state=42)
    cv_scores = cross_val_score(model, x_train, y_train, cv=cv, scoring="accuracy", n_jobs=-1)
    return {
        "cv_mean_accuracy": float(cv_scores.mean()),
        "cv_std_accuracy": float(cv_scores.std()),
    }


def plot_accuracy_comparison(results: dict[str, dict]) -> None:
    labels = list(results.keys())
    scores = [results[name]["accuracy"] for name in labels]

    plt.figure(figsize=(8, 5))
    bars = plt.bar(labels, scores, color=["#7c5cff", "#22c55e"])
    plt.title("FinSet Model Accuracy Comparison")
    plt.ylabel("Accuracy")
    plt.ylim(0, 1)
    for bar, score in zip(bars, scores):
        plt.text(bar.get_x() + bar.get_width() / 2, score + 0.02, f"{score:.2f}", ha="center")
    plt.tight_layout()
    plt.savefig(ARTIFACTS_DIR / "accuracy_comparison.png", dpi=200)
    plt.close()


def plot_feature_importance(model: Pipeline, feature_names: list[str]) -> None:
    classifier = model.named_steps["classifier"]
    importances = classifier.feature_importances_
    top_indices = np.argsort(importances)[-10:]

    top_features = [feature_names[i] for i in top_indices]
    top_importances = importances[top_indices]

    plt.figure(figsize=(10, 6))
    plt.barh(top_features, top_importances, color="#8b5cf6")
    plt.title("Random Forest Feature Importance")
    plt.xlabel("Importance Score")
    plt.tight_layout()
    plt.savefig(ARTIFACTS_DIR / "rf_feature_importance.png", dpi=200)
    plt.close()


def main() -> None:
    df = load_and_prepare_dataset(DATA_PATH)

    feature_columns = [
        "Description",
        "Category",
        "TransactionType",
        "DayOfWeek",
        "Month",
        "Amount",
        "Balance",
        "Day",
        "IsWeekend",
        "SavingsRatio",
        "ExpenseToBalanceRatio",
    ]
    target_column = "BehaviorRisk"

    x = df[feature_columns]
    y = df[target_column]

    categorical_features = ["Description", "Category", "TransactionType", "DayOfWeek", "Month"]
    numerical_features = ["Amount", "Balance", "Day", "IsWeekend", "SavingsRatio", "ExpenseToBalanceRatio"]

    print("=" * 72)
    print("STEP 3: TRAIN / TEST SPLIT")
    print("=" * 72)
    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=0.20,
        random_state=42,
        stratify=y,
    )
    print(f"Training samples   : {len(x_train)}")
    print(f"Testing samples    : {len(x_test)}")
    print()

    preprocessor = build_preprocessor(categorical_features, numerical_features)

    models: dict[str, dict] = {
        "Random Forest Classifier": {
            "estimator": RandomForestClassifier(random_state=42),
            "params": {
                "classifier__n_estimators": [100, 200, 300],
                "classifier__max_depth": [4, 6, 8, None],
                "classifier__min_samples_split": [2, 4],
                "classifier__min_samples_leaf": [1, 2],
                "classifier__class_weight": [None, "balanced"],
            },
        },
        "Logistic Regression": {
            "estimator": LogisticRegression(
                max_iter=2000,
                random_state=42,
            ),
            "params": {
                "classifier__C": [0.01, 0.1, 1, 5, 10],
                "classifier__solver": ["liblinear", "lbfgs"],
                "classifier__class_weight": [None, "balanced"],
            },
        },
        "Support Vector Machine": {
            "estimator": SVC(probability=True, random_state=42),
            "params": {
                "classifier__C": [0.1, 1, 5, 10],
                "classifier__kernel": ["linear", "rbf"],
                "classifier__gamma": ["scale", "auto"],
            },
        },
        "Gradient Boosting": {
            "estimator": GradientBoostingClassifier(random_state=42),
            "params": {
                "classifier__n_estimators": [50, 100, 150],
                "classifier__learning_rate": [0.03, 0.05, 0.1],
                "classifier__max_depth": [2, 3],
            },
        },
    }

    if XGBOOST_AVAILABLE:
        models["XGBoost Classifier"] = {
            "estimator": XGBClassifier(
                random_state=42,
                eval_metric="logloss",
                use_label_encoder=False,
            ),
            "params": {
                "classifier__n_estimators": [50, 100, 200],
                "classifier__max_depth": [2, 3, 4],
                "classifier__learning_rate": [0.03, 0.1, 0.2],
                "classifier__subsample": [0.8, 1.0],
            },
        }

    trained_models: dict[str, Pipeline] = {}
    results: dict[str, dict] = {}
    tuning_results: dict[str, dict] = {}
    cv_results: dict[str, dict] = {}

    print("=" * 72)
    print("STEP 4: MODEL TRAINING")
    print("=" * 72)
    for name, config in models.items():
        pipeline = Pipeline(
            steps=[
                ("preprocessor", preprocessor),
                ("classifier", config["estimator"]),
            ]
        )
        tuned_model, tuning_info = tune_model(
            name,
            pipeline,
            config["params"],
            x_train,
            y_train,
        )
        trained_models[name] = tuned_model
        tuning_results[name] = tuning_info
        cv_results[name] = compute_cross_validation_metrics(tuned_model, x_train, y_train)
        results[name] = evaluate_model(name, tuned_model, x_test, y_test)

    summary_rows = []
    report_rows = []
    for model_name, metrics in results.items():
        summary_rows.append(
            {
                "Model": model_name,
                "Accuracy": round(metrics["accuracy"], 4),
                "Precision": round(metrics["precision"], 4),
                "Recall": round(metrics["recall"], 4),
                "F1_Score": round(metrics["f1_score"], 4),
                "Best_CV_Accuracy": round(tuning_results[model_name]["best_cv_accuracy"], 4),
                "CV_Mean_Accuracy": round(cv_results[model_name]["cv_mean_accuracy"], 4),
                "CV_Std_Accuracy": round(cv_results[model_name]["cv_std_accuracy"], 4),
                "TN": metrics["confusion_matrix"][0][0],
                "FP": metrics["confusion_matrix"][0][1],
                "FN": metrics["confusion_matrix"][1][0],
                "TP": metrics["confusion_matrix"][1][1],
            }
        )
        for label, report_values in metrics["classification_report_dict"].items():
            if isinstance(report_values, dict):
                report_rows.append(
                    {
                        "Model": model_name,
                        "Label": label,
                        "Precision": round(report_values.get("precision", 0), 4),
                        "Recall": round(report_values.get("recall", 0), 4),
                        "F1_Score": round(report_values.get("f1-score", 0), 4),
                        "Support": report_values.get("support", 0),
                    }
                )

    results_df = pd.DataFrame(summary_rows).sort_values(
        by=["Accuracy", "F1_Score"], ascending=False
    ).reset_index(drop=True)
    results_df.index = results_df.index + 1
    results_df.index.name = "Rank"

    detailed_report_df = pd.DataFrame(report_rows)

    best_model_name = results_df.iloc[0]["Model"]
    best_model = trained_models[best_model_name]

    print("=" * 72)
    print("STEP 5: MODEL COMPARISON")
    print("=" * 72)
    print(results_df.to_string())
    print(f"Best model selected           : {best_model_name}")
    print()

    joblib.dump(best_model, MODEL_PATH)
    print("=" * 72)
    print("STEP 6: MODEL SAVED")
    print("=" * 72)
    print(f"Saved model file              : {MODEL_PATH.name}")
    print(f"Full path                     : {MODEL_PATH}")
    print()

    sample_input = pd.DataFrame(
        [
            {
                "Description": "Online Shopping Purchase",
                "Category": "Shopping",
                "TransactionType": "debit",
                "DayOfWeek": "Friday",
                "Month": "July",
                "Amount": 2800,
                "Balance": 18500,
                "Day": 12,
                "IsWeekend": 0,
                "SavingsRatio": 0.05,
                "ExpenseToBalanceRatio": 2800 / 18500,
            }
        ]
    )

    predicted_class = int(best_model.predict(sample_input)[0])
    predicted_label = "High Financial Risk Behavior" if predicted_class == 1 else "Low Financial Risk Behavior"

    print("=" * 72)
    print("STEP 7: TEST PREDICTION")
    print("=" * 72)
    print("Sample Input:")
    print(sample_input.to_string(index=False))
    print()
    print(f"Predicted Class              : {predicted_class}")
    print(f"Predicted Meaning            : {predicted_label}")
    print()

    plot_accuracy_comparison(results)

    rf_pipeline = trained_models["Random Forest Classifier"]
    transformed_feature_names = list(
        rf_pipeline.named_steps["preprocessor"].get_feature_names_out()
    )
    plot_feature_importance(rf_pipeline, transformed_feature_names)

    report_payload = {
        "best_model": best_model_name,
        "results_table": results_df.reset_index().to_dict(orient="records"),
        "results": {
            name: {
                key: value
                for key, value in metrics.items()
                if key not in {"classification_report", "classification_report_dict"}
            }
            for name, metrics in results.items()
        },
        "tuning_results": tuning_results,
        "cross_validation_results": cv_results,
        "sample_prediction": {
            "predicted_class": predicted_class,
            "predicted_label": predicted_label,
        },
    }

    with open(ARTIFACTS_DIR / "training_report.json", "w", encoding="utf-8") as fp:
        json.dump(report_payload, fp, indent=2)

    results_df.to_csv(ARTIFACTS_DIR / "model_results_summary.csv")
    detailed_report_df.to_csv(ARTIFACTS_DIR / "classification_report_detailed.csv", index=False)

    print("=" * 72)
    print("STEP 8: REPORT ARTIFACTS GENERATED")
    print("=" * 72)
    print(f"Accuracy chart               : {ARTIFACTS_DIR / 'accuracy_comparison.png'}")
    print(f"Feature importance chart     : {ARTIFACTS_DIR / 'rf_feature_importance.png'}")
    print(f"Results dataframe (CSV)      : {ARTIFACTS_DIR / 'model_results_summary.csv'}")
    print(f"Detailed report dataframe    : {ARTIFACTS_DIR / 'classification_report_detailed.csv'}")
    print(f"JSON metrics report          : {ARTIFACTS_DIR / 'training_report.json'}")
    print()


if __name__ == "__main__":
    main()
