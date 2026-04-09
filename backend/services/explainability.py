from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from xgboost import DMatrix

try:
    import shap  # type: ignore

    SHAP_AVAILABLE = True
except Exception:
    shap = None
    SHAP_AVAILABLE = False

ARTIFACTS_DIR = Path(__file__).resolve().parents[1] / "artifacts"
SHAP_SUMMARY_PATH = ARTIFACTS_DIR / "shap_summary.json"
SHAP_VALUES_PATH = ARTIFACTS_DIR / "shap_values.json"


def explain_tree_prediction(model, latest_features, feature_columns: list[str]) -> dict:
    try:
        scaler = model.named_steps["scaler"]
        regressor = model.named_steps["regressor"]
        scaled = scaler.transform(latest_features)
    except Exception:
        return {"method": "unavailable", "feature_importance": [], "contributions": []}

    if SHAP_AVAILABLE:
        try:
            explainer = shap.TreeExplainer(regressor)
            shap_values = explainer.shap_values(scaled)
            values = shap_values[0] if hasattr(shap_values, "__len__") else shap_values
            ranked = sorted(
                (
                    {
                        "feature": feature_columns[index],
                        "impact": round(float(values[index]), 4),
                        "absolute_impact": round(abs(float(values[index])), 4),
                    }
                    for index in range(min(len(feature_columns), len(values)))
                ),
                key=lambda item: item["absolute_impact"],
                reverse=True,
            )
            return {
                "method": "shap",
                "feature_importance": ranked[:5],
                "contributions": ranked[:5],
            }
        except Exception:
            pass

    try:
        contributions = regressor.get_booster().predict(DMatrix(scaled, feature_names=feature_columns), pred_contribs=True)[0]
        ranked = sorted(
            (
                {
                    "feature": feature_columns[index],
                    "impact": round(float(contributions[index]), 4),
                    "absolute_impact": round(abs(float(contributions[index])), 4),
                }
                for index in range(min(len(feature_columns), len(contributions) - 1))
            ),
            key=lambda item: item["absolute_impact"],
            reverse=True,
        )
        return {
            "method": "xgboost_contrib",
            "feature_importance": ranked[:5],
            "contributions": ranked[:5],
        }
    except Exception:
        return {"method": "unavailable", "feature_importance": [], "contributions": []}


def explain_ensemble(models: dict, latest_features, feature_columns: list[str]) -> dict:
    explanations = {}
    for name, model in models.items():
        if name == "lstm":
            explanations[name] = {
                "method": "sequence_model",
                "feature_importance": [],
                "contributions": [],
                "note": "Sequence model explanation is summarized through ensemble confidence in the current runtime.",
            }
            continue
        explanations[name] = explain_tree_prediction(model, latest_features, feature_columns)
    result = {
        "shap_available": SHAP_AVAILABLE,
        "models": explanations,
    }
    try:
        ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
        SHAP_SUMMARY_PATH.write_text(json.dumps(result, indent=2), encoding="utf-8")
        compact_values = {
            model_name: model_info.get("contributions", [])
            for model_name, model_info in explanations.items()
        }
        SHAP_VALUES_PATH.write_text(json.dumps(compact_values, indent=2), encoding="utf-8")
    except Exception:
        pass
    return result
