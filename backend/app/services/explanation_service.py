"""Explain the exact held-out model used for a player's displayed estimate.
Tree models use SHAP; standardized Ridge models use coefficient contributions
relative to the training mean. The empirical screening buffer is separate.
"""

import json
from functools import lru_cache
from pathlib import Path

import lightgbm as lgb
import joblib
import numpy as np
import pandas as pd
import shap

from app.services import data_store
from app.utils.model_features import build_matrix, feature_group, feature_label

ARTIFACTS = Path(__file__).resolve().parent.parent.parent / "model" / "artifacts"

TOP_N_CONTRIBUTIONS = 8


@lru_cache(maxsize=10)
def _fold_model(group, fold):
    prefix = f"{group}_fold_{fold}"
    meta = json.loads((ARTIFACTS / f"{prefix}.json").read_text())
    if meta["method"] == "lightgbm":
        model = shap.TreeExplainer(lgb.Booster(model_file=str(ARTIFACTS / f"{prefix}.txt")))
    else:
        model = joblib.load(ARTIFACTS / f"{prefix}.joblib")
    return meta["method"], model, meta["features"]


def explain_player(player_id: int) -> dict | None:
    players = data_store.load_players()
    match = players[players["player_id"] == player_id]
    if match.empty or not match.iloc[0]["meets_minutes_threshold"]:
        return None

    row = match.iloc[0]
    group = "goalkeepers" if row["position_group"] == "GK" else "outfield"
    method, model, feature_cols = _fold_model(group, int(row["model_fold"]))

    X = build_matrix(match, feature_cols)

    if method == "lightgbm":
        shap_values = np.asarray(model.shap_values(X))[0]
        base_value = model.expected_value
        base_value = base_value[0] if hasattr(base_value, "__len__") else base_value
    else:
        imputer = model.named_steps["simpleimputer"]
        scaler = model.named_steps["standardscaler"]
        lr = model.named_steps["ridge"]
        transformed = scaler.transform(imputer.transform(X))[0]
        shap_values = lr.coef_ * transformed
        base_value = lr.intercept_

    predicted_log = base_value + shap_values.sum()

    contributions = []
    for col, raw_value, impact in zip(feature_cols, X.iloc[0], shap_values):
        contributions.append({
            "feature": col,
            "label": feature_label(col),
            "player_value": None if pd.isna(raw_value) else round(float(raw_value), 3),
            "impact": round(float(impact), 4),
            "direction": "positive" if impact >= 0 else "negative",
        })
    groups = {}
    for c in contributions:
        name = feature_group(c["feature"])
        groups[name] = groups.get(name, 0.0) + c["impact"]
    group_list = sorted(({"group": g, "impact": round(v, 4)} for g, v in groups.items()),
                        key=lambda g: abs(g["impact"]), reverse=True)
    contributions.sort(key=lambda c: abs(c["impact"]), reverse=True)

    return {
        "predicted_value_eur": float(np.expm1(predicted_log)),
        "base_value_eur": float(np.expm1(base_value)),
        "model_type": method,
        "contributions": contributions[:TOP_N_CONTRIBUTIONS],
        # Every feature's contribution summed by plain-language theme.
        "groups": group_list,
    }
