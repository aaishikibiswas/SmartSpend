from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix, hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier


CATEGORY_MAP = {
    "Housing": ["rent", "mortgage", "electricity", "water", "internet", "maintenance", "landlord", "property tax", "apartment"],
    "Food": ["restaurant", "swiggy", "zomato", "cafe", "kitchen", "bakery", "grocery", "supermarket", "dining", "coffee", "tea", "snacks"],
    "Transport": ["uber", "ola", "petrol", "fuel", "flight", "train", "metro", "cab", "bus", "parking", "toll"],
    "Shopping": ["amazon", "flipkart", "myntra", "apple", "store", "mall", "purchase", "electronics", "fashion", "retail"],
    "Entertainment": ["netflix", "amazon prime", "spotify", "movie", "bookmyshow", "gaming", "concert", "subscription", "streaming"],
    "Healthcare": ["pharmacy", "hospital", "clinic", "fitness", "gym", "doctor", "medical", "lab", "apollo", "medicine"],
    "Income": ["salary", "freelance", "refund", "credit", "interest", "dividend", "bonus", "incentive", "deposit"],
}

ARTIFACTS_DIR = Path(__file__).resolve().parents[1] / "artifacts"
EVALUATION_PATH = ARTIFACTS_DIR / "categorizer_evaluation.json"

_STATE: dict[str, object] = {
    "vectorizer": None,
    "classifier": None,
    "labels": [],
    "evaluation": {},
}
_CONFIDENCE_THRESHOLD = 0.34


def _normalize_text(text: str) -> str:
    value = str(text or "").lower().strip()
    value = re.sub(r"[^a-z0-9\s&/-]", " ", value)
    value = re.sub(r"\s+", " ", value)
    return value


def _seed_corpus() -> tuple[list[str], list[str], list[list[float]]]:
    texts: list[str] = []
    labels: list[str] = []
    tabular: list[list[float]] = []
    templates = ["{kw}", "{kw} payment", "{kw} bill", "{kw} charge", "{kw} purchase", "paid for {kw}", "{kw} transaction", "monthly {kw}"]
    for category, keywords in CATEGORY_MAP.items():
        base_amount = 1500 if category not in {"Income", "Housing"} else (12000 if category == "Income" else 4500)
        for keyword in keywords:
            for template in templates:
                text = _normalize_text(template.format(kw=keyword))
                texts.append(text)
                labels.append(category)
                tabular.append([base_amount, len(text.split()), 15.0, 0.0])
    return texts, labels, tabular


def _historical_corpus() -> tuple[list[str], list[str], list[list[float]]]:
    try:
        from backend.storage import Storage

        df = Storage.get_transactions()
    except Exception:
        return [], [], []

    if df.empty or "merchant" not in df.columns or "category" not in df.columns:
        return [], [], []

    history = df.copy()
    history["merchant"] = history["merchant"].astype(str)
    history["category"] = history["category"].astype(str)
    history = history[history["merchant"].str.strip() != ""]
    history = history[history["category"].str.strip() != ""]
    history = history[history["category"].str.lower() != "other"]

    texts = [_normalize_text(value) for value in history["merchant"].tolist()]
    labels = [value.title() for value in history["category"].tolist()]
    tabular = [
        [
            abs(float(row.get("amount", 0))),
            len(_normalize_text(row.get("merchant", "")).split()),
            float(pd.to_datetime(row.get("date"), errors="coerce").month or 0),
            1.0 if float(row.get("amount", 0)) > 0 else 0.0,
        ]
        for _, row in history.iterrows()
    ]
    return texts, labels, tabular


def _rule_based_fallback(description: str) -> str:
    text = _normalize_text(description)
    for category, keywords in CATEGORY_MAP.items():
        for keyword in keywords:
            if re.search(rf"\b{re.escape(keyword)}\b", text):
                return category
    return "Other"


def _make_classifier() -> XGBClassifier:
    return XGBClassifier(
        n_estimators=120,
        max_depth=5,
        learning_rate=0.1,
        subsample=0.95,
        colsample_bytree=0.95,
        objective="multi:softprob",
        eval_metric="mlogloss",
        random_state=42,
    )


def _metric_pack(y_true: np.ndarray, y_pred: np.ndarray) -> dict[str, float]:
    precision, recall, f1, _ = precision_recall_fscore_support(y_true, y_pred, average="macro", zero_division=0)
    return {
        "accuracy": round(float(accuracy_score(y_true, y_pred)), 4),
        "precision_macro": round(float(precision), 4),
        "recall_macro": round(float(recall), 4),
        "f1_macro": round(float(f1), 4),
    }


def _write_evaluation(report: dict[str, object]) -> None:
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    EVALUATION_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")


def _ensure_model() -> None:
    if _STATE["classifier"] is not None and _STATE["vectorizer"] is not None:
        return

    seed_texts, seed_labels, seed_tabular = _seed_corpus()
    history_texts, history_labels, history_tabular = _historical_corpus()
    texts = seed_texts + history_texts
    labels = seed_labels + history_labels
    tabular = seed_tabular + history_tabular

    vectorizer = TfidfVectorizer(ngram_range=(1, 2), lowercase=True, strip_accents="unicode", sublinear_tf=True, min_df=1)
    label_names = list(dict.fromkeys(labels))
    label_to_index = {label: idx for idx, label in enumerate(label_names)}
    y_all = np.asarray([label_to_index[label] for label in labels], dtype=int)
    stratify_target = y_all if min(Counter(y_all).values()) >= 2 else None

    if len(texts) >= 30:
        train_idx, temp_idx = train_test_split(
            np.arange(len(texts)),
            test_size=0.4,
            random_state=42,
            stratify=stratify_target,
        )
        temp_stratify = y_all[temp_idx] if stratify_target is not None and min(Counter(y_all[temp_idx]).values()) >= 2 else None
        val_idx, test_idx = train_test_split(
            temp_idx,
            test_size=0.5,
            random_state=42,
            stratify=temp_stratify,
        )

        train_texts = [texts[index] for index in train_idx]
        val_texts = [texts[index] for index in val_idx]
        test_texts = [texts[index] for index in test_idx]

        train_tabular = np.asarray([tabular[index] for index in train_idx], dtype=float)
        val_tabular = np.asarray([tabular[index] for index in val_idx], dtype=float)
        test_tabular = np.asarray([tabular[index] for index in test_idx], dtype=float)

        y_train = y_all[train_idx]
        y_val = y_all[val_idx]
        y_test = y_all[test_idx]

        train_text_features = vectorizer.fit_transform(train_texts)
        val_text_features = vectorizer.transform(val_texts)
        test_text_features = vectorizer.transform(test_texts)

        train_features = hstack([train_text_features, csr_matrix(train_tabular)])
        val_features = hstack([val_text_features, csr_matrix(val_tabular)])
        test_features = hstack([test_text_features, csr_matrix(test_tabular)])

        eval_classifier = _make_classifier()
        eval_classifier.fit(train_features, y_train)
        val_predictions = eval_classifier.predict(val_features)
        test_predictions = eval_classifier.predict(test_features)

        _STATE["evaluation"] = {
            "data_split": {
                "strategy": "stratified_train_validation_test",
                "train_rows": int(len(train_idx)),
                "validation_rows": int(len(val_idx)),
                "test_rows": int(len(test_idx)),
            },
            "validation": _metric_pack(y_val, val_predictions),
            "test": _metric_pack(y_test, test_predictions),
            "classes": label_names,
        }
    else:
        text_features = vectorizer.fit_transform(texts)
        _STATE["evaluation"] = {
            "data_split": {
                "strategy": "not_enough_data",
                "train_rows": len(texts),
                "validation_rows": 0,
                "test_rows": 0,
            },
            "validation": {},
            "test": {},
            "classes": label_names,
            "note": "Insufficient labeled rows for a separate validation/test split.",
        }

    full_text_features = vectorizer.fit_transform(texts)
    full_numeric_features = csr_matrix(np.asarray(tabular, dtype=float))
    full_features = hstack([full_text_features, full_numeric_features])

    classifier = _make_classifier()
    classifier.fit(full_features, y_all)

    _STATE["vectorizer"] = vectorizer
    _STATE["classifier"] = classifier
    _STATE["labels"] = label_names
    _write_evaluation(
        {
            "task": "transaction_categorization",
            "model_family": "hybrid_tfidf_tabular_xgboost",
            "evaluation": _STATE["evaluation"],
        }
    )


def predict_transaction_category(description: str, amount: float | None = None, date: str | None = None) -> dict:
    text = _normalize_text(description)
    if not text:
        return {"category": "Other", "confidence": 0.0}

    try:
        _ensure_model()
        vectorizer = _STATE["vectorizer"]
        classifier = _STATE["classifier"]
        labels = _STATE["labels"]
        text_features = vectorizer.transform([text])
        parsed_date = pd.to_datetime(date, errors="coerce")
        numeric_features = csr_matrix(
            [
                [
                    abs(float(amount or 0)),
                    len(text.split()),
                    float(parsed_date.month if not pd.isna(parsed_date) else 0),
                    1.0 if float(amount or 0) > 0 else 0.0,
                ]
            ],
            dtype=float,
        )
        combined = hstack([text_features, numeric_features])
        probabilities = classifier.predict_proba(combined)[0]
        best_index = int(np.argmax(probabilities))
        best_label = str(labels[best_index]).title()
        best_score = float(probabilities[best_index])
        if best_score >= _CONFIDENCE_THRESHOLD:
            return {"category": best_label, "confidence": round(best_score, 4)}
    except Exception:
        pass

    fallback = _rule_based_fallback(text)
    return {"category": fallback, "confidence": 0.32 if fallback != "Other" else 0.0}


def categorize_transaction(description: str, amount: float | None = None, date: str | None = None) -> str:
    return predict_transaction_category(description, amount=amount, date=date)["category"]


def categorize_transactions_dataframe(df: pd.DataFrame, source_column: str = "merchant") -> pd.Series:
    if df.empty or source_column not in df.columns:
        return pd.Series(dtype=str)
    return df.apply(lambda row: categorize_transaction(row.get(source_column, ""), amount=row.get("amount"), date=row.get("date")), axis=1)


def get_categorizer_evaluation() -> dict[str, object]:
    _ensure_model()
    return dict(_STATE.get("evaluation", {}))
