from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pandas as pd
from matplotlib import pyplot as plt
from matplotlib.backends.backend_pdf import PdfPages


ROOT_DIR = Path(__file__).resolve().parent
ARTIFACTS_DIR = ROOT_DIR / "artifacts"
REPORT_JSON = ARTIFACTS_DIR / "training_report.json"
SUMMARY_CSV = ARTIFACTS_DIR / "model_results_summary.csv"
DETAIL_CSV = ARTIFACTS_DIR / "classification_report_detailed.csv"
ACCURACY_CHART = ARTIFACTS_DIR / "accuracy_comparison.png"
FEATURE_IMPORTANCE_CHART = ARTIFACTS_DIR / "rf_feature_importance.png"
PDF_REPORT = ARTIFACTS_DIR / "FinSet_Model_Evaluation_Report.pdf"


def add_title_page(pdf: PdfPages, payload: dict) -> None:
    fig = plt.figure(figsize=(8.27, 11.69))
    fig.patch.set_facecolor("white")
    plt.axis("off")

    best_model = payload.get("best_model", "N/A")
    sample = payload.get("sample_prediction", {})

    fig.text(0.08, 0.93, "FinSet Model Training & Evaluation Report", fontsize=22, weight="bold")
    fig.text(0.08, 0.89, "AI-Powered Financial Behavior Prediction System", fontsize=13, color="#444444")

    fig.text(0.08, 0.80, "Report Overview", fontsize=16, weight="bold")
    overview = (
        "This report documents the machine learning workflow used in FinSet for "
        "financial behavior prediction. It includes dataset preprocessing, model "
        "training, evaluation metrics, model comparison, visual analysis, and a "
        "sample prediction generated from the trained best-performing model."
    )
    fig.text(0.08, 0.74, textwrap.fill(overview, width=80), fontsize=11, va="top")

    fig.text(0.08, 0.61, f"Best Model Selected : {best_model}", fontsize=12)
    fig.text(0.08, 0.57, f"Sample Prediction   : {sample.get('predicted_label', 'N/A')}", fontsize=12)
    fig.text(0.08, 0.53, f"Predicted Class     : {sample.get('predicted_class', 'N/A')}", fontsize=12)

    fig.text(0.08, 0.43, "Included Sections", fontsize=16, weight="bold")
    sections = [
        "1. Model comparison summary",
        "2. Detailed classification evaluation",
        "3. Accuracy comparison chart",
        "4. Random Forest feature importance",
        "5. Interpretation and academic explanation",
    ]
    for idx, line in enumerate(sections):
        fig.text(0.10, 0.39 - idx * 0.04, line, fontsize=11)

    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def add_dataframe_page(pdf: PdfPages, title: str, dataframe: pd.DataFrame, font_size: int = 10) -> None:
    fig, ax = plt.subplots(figsize=(11.69, 8.27))
    fig.patch.set_facecolor("white")
    ax.axis("off")
    ax.set_title(title, fontsize=16, weight="bold", pad=20)

    df = dataframe.copy()
    table = ax.table(
        cellText=df.values,
        colLabels=df.columns,
        cellLoc="center",
        loc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(font_size)
    table.scale(1.15, 1.6)

    for (row, col), cell in table.get_celld().items():
        if row == 0:
            cell.set_text_props(weight="bold", color="white")
            cell.set_facecolor("#4f46e5")
        else:
            cell.set_facecolor("#f8f9fb" if row % 2 == 0 else "#ffffff")

    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def add_image_page(pdf: PdfPages, title: str, image_path: Path) -> None:
    fig, ax = plt.subplots(figsize=(11.69, 8.27))
    fig.patch.set_facecolor("white")
    ax.axis("off")
    ax.set_title(title, fontsize=16, weight="bold", pad=20)

    image = plt.imread(image_path)
    ax.imshow(image)

    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def add_explanation_page(pdf: PdfPages) -> None:
    fig = plt.figure(figsize=(8.27, 11.69))
    fig.patch.set_facecolor("white")
    plt.axis("off")

    fig.text(0.08, 0.94, "Model Explanation for Academic Documentation", fontsize=18, weight="bold")

    sections = [
        (
            "Model Used",
            "Two classification models were trained: Random Forest Classifier and "
            "Logistic Regression. The final best model was selected based on test accuracy.",
        ),
        (
            "How Training Works",
            "The dataset is loaded from CSV, missing values are cleaned, categorical "
            "variables are encoded using OneHotEncoder, and numerical features are "
            "standardized. The data is then split into 80% training and 20% testing "
            "before fitting both models.",
        ),
        (
            "Meaning of Accuracy",
            "Accuracy represents the proportion of correct predictions made by the model "
            "on unseen test data. For example, an accuracy of 0.75 means the model "
            "correctly predicted 75% of the test instances.",
        ),
        (
            "Why This Model Is Suitable",
            "Random Forest is suitable for financial prediction because it handles mixed "
            "feature types, captures non-linear relationships, and provides feature "
            "importance values useful for financial interpretation. Logistic Regression "
            "serves as a reliable baseline for comparison.",
        ),
        (
            "Conclusion",
            "The trained FinSet model can be used to classify financial behavior risk "
            "based on transaction patterns. The evaluation metrics, confusion matrix, "
            "and feature importance support both model performance analysis and academic reporting.",
        ),
    ]

    y = 0.86
    for heading, body in sections:
        fig.text(0.08, y, heading, fontsize=13, weight="bold")
        fig.text(0.08, y - 0.035, textwrap.fill(body, width=85), fontsize=10.5, va="top")
        y -= 0.16

    disclaimer = (
        "Note: The current workspace dataset is small, so the reported metrics are suitable "
        "for demonstration and coursework documentation, but a larger dataset is recommended "
        "for stronger generalization."
    )
    fig.text(0.08, 0.11, textwrap.fill(disclaimer, width=90), fontsize=10, style="italic", color="#555555")

    pdf.savefig(fig, bbox_inches="tight")
    plt.close(fig)


def main() -> None:
    if not REPORT_JSON.exists():
        raise FileNotFoundError("training_report.json not found. Run train.py first.")

    with open(REPORT_JSON, "r", encoding="utf-8") as fp:
        payload = json.load(fp)

    summary_df = pd.read_csv(SUMMARY_CSV)
    detail_df = pd.read_csv(DETAIL_CSV)

    with PdfPages(PDF_REPORT) as pdf:
        add_title_page(pdf, payload)
        add_dataframe_page(pdf, "Model Comparison Summary", summary_df, font_size=10)
        add_dataframe_page(pdf, "Detailed Classification Report", detail_df, font_size=9)
        add_image_page(pdf, "Accuracy Comparison Chart", ACCURACY_CHART)
        add_image_page(pdf, "Random Forest Feature Importance", FEATURE_IMPORTANCE_CHART)
        add_explanation_page(pdf)

    print("=" * 72)
    print("PDF REPORT GENERATED SUCCESSFULLY")
    print("=" * 72)
    print(f"PDF Path : {PDF_REPORT}")
    print()


if __name__ == "__main__":
    main()
