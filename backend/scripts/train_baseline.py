"""
Baseline models for the market-value regression, evaluated before LightGBM
so the jump to gradient boosting (Phase 6) is justified by a number, not an
assertion.

Two baselines per position group (outfield, goalkeepers):
  - Mean prediction (DummyRegressor): the floor any real model must beat.
  - Linear regression: a simple, interpretable model. If this already
    captures most of the signal, LightGBM wouldn't be worth the added
    complexity.

Evaluation is 5-fold cross-validation rather than a single train/test split:
with ~1,339 outfield and 113 goalkeeper rows, a single 20% holdout is small
enough that its score depends heavily on which players happen to land in it.
Out-of-fold predictions (cross_val_predict) give every player exactly one
held-out prediction, using the full dataset without leakage.

Usage: python scripts/train_baseline.py (run engineer_features.py first)
"""

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.dummy import DummyRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, r2_score, root_mean_squared_error
from sklearn.model_selection import KFold, cross_val_predict
from sklearn.pipeline import Pipeline

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.utils.features import OUTFIELD_FEATURES, GOALKEEPER_FEATURES, modelling_groups  # noqa: E402

DATA_PROCESSED = Path(__file__).resolve().parent.parent / "data" / "processed"
RANDOM_SEED = 42


def evaluate(model, X, y, label):
    cv = KFold(n_splits=5, shuffle=True, random_state=RANDOM_SEED)
    pred_log = cross_val_predict(model, X, y, cv=cv)

    mae_log = mean_absolute_error(y, pred_log)
    r2_log = r2_score(y, pred_log)

    actual_eur = np.expm1(y)
    pred_eur = np.expm1(pred_log)
    mae_eur = mean_absolute_error(actual_eur, pred_eur)
    rmse_eur = root_mean_squared_error(actual_eur, pred_eur)
    r2_eur = r2_score(actual_eur, pred_eur)

    print(f"{label}")
    print(f"  log-space:  MAE={mae_log:.3f}  R2={r2_log:.3f}")
    print(f"  EUR-space:  MAE=€{mae_eur:,.0f}  RMSE=€{rmse_eur:,.0f}  R2={r2_eur:.3f}")
    return {"label": label, "mae_eur": mae_eur, "rmse_eur": rmse_eur, "r2_eur": r2_eur}


def run_group(df, feature_cols, group_name):
    df = df.copy()
    if "position_group" in df.columns and df["position_group"].nunique() > 1:
        dummies = pd.get_dummies(df["position_group"], prefix="pos")
        df = pd.concat([df, dummies], axis=1)
        feature_cols = feature_cols + list(dummies.columns)

    X = df[feature_cols]
    y = df["log_market_value"]

    print(f"\n=== {group_name} (n={len(df)}, {len(feature_cols)} features) ===")
    mean_model = DummyRegressor(strategy="mean")
    mean_result = evaluate(mean_model, X, y, "Mean prediction (baseline floor)")

    linreg = Pipeline([
        ("impute", SimpleImputer(strategy="median")),
        ("model", LinearRegression()),
    ])
    linreg_result = evaluate(linreg, X, y, "Linear regression")
    return {"n": len(df), "mean_baseline": mean_result, "linear_regression": linreg_result}


def main():
    df = pd.read_csv(DATA_PROCESSED / "players_features.csv")
    reliable = df[df["meets_minutes_threshold"]]

    groups = modelling_groups(reliable)
    outfield, keepers = groups["outfield"], groups["goalkeepers"]

    results = {
        "outfield": run_group(outfield, OUTFIELD_FEATURES, "Outfield players"),
        "goalkeepers": run_group(keepers, GOALKEEPER_FEATURES, "Goalkeepers"),
    }

    artifacts_dir = Path(__file__).resolve().parent.parent / "model" / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    (artifacts_dir / "baseline_metrics.json").write_text(json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
