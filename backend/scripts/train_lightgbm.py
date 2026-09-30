"""
Trains the LightGBM valuation models (outfield, goalkeepers) and evaluates
them the same way as the baselines (5-fold CV, out-of-fold predictions) for
a fair comparison.

Hyperparameters are chosen for the small-data regime here (1,339 outfield /
113 goalkeeper rows), not searched: shallow trees and a small leaf count keep
the model from memorizing individual players, and L1/L2 regularization plus
row/column subsampling add further protection against overfitting. This is
a deliberately conservative starting point rather than a tuned optimum. An
exhaustive grid search over ~1,300 rows would mostly be fitting noise.

After evaluation, each model is refit on 100% of its reliable-minutes data
(cross-validation was only for the honest performance estimate) and saved
for the API to load directly, rather than retraining on every server start.

Usage: python scripts/train_lightgbm.py (run engineer_features.py and
train_baseline.py first)
"""

import json
import sys
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, r2_score, root_mean_squared_error
from sklearn.model_selection import KFold, cross_val_predict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.utils.features import OUTFIELD_FEATURES, GOALKEEPER_FEATURES, modelling_groups  # noqa: E402

DATA_PROCESSED = Path(__file__).resolve().parent.parent / "data" / "processed"
ARTIFACTS = Path(__file__).resolve().parent.parent / "model" / "artifacts"
RANDOM_SEED = 42

OUTFIELD_PARAMS = dict(
    n_estimators=200, learning_rate=0.04, num_leaves=15, max_depth=4,
    min_child_samples=20, subsample=0.8, colsample_bytree=0.8,
    reg_alpha=0.1, reg_lambda=0.1, random_state=RANDOM_SEED, verbosity=-1,
)
GOALKEEPER_PARAMS = dict(
    n_estimators=120, learning_rate=0.04, num_leaves=7, max_depth=3,
    min_child_samples=10, subsample=0.8, colsample_bytree=0.8,
    reg_alpha=0.1, reg_lambda=0.1, random_state=RANDOM_SEED, verbosity=-1,
)


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

    print(f"  {label}")
    print(f"    log-space:  MAE={mae_log:.3f}  R2={r2_log:.3f}")
    print(f"    EUR-space:  MAE=€{mae_eur:,.0f}  RMSE=€{rmse_eur:,.0f}  R2={r2_eur:.3f}")
    return {"label": label, "mae_log": mae_log, "r2_log": r2_log,
            "mae_eur": mae_eur, "rmse_eur": rmse_eur, "r2_eur": r2_eur}


def run_group(df, feature_cols, params, group_name, model_filename):
    df = df.copy()
    if df["position_group"].nunique() > 1:
        dummies = pd.get_dummies(df["position_group"], prefix="pos")
        df = pd.concat([df, dummies], axis=1)
        feature_cols = feature_cols + list(dummies.columns)

    X = df[feature_cols]
    y = df["log_market_value"]

    print(f"\n=== {group_name} (n={len(df)}, {len(feature_cols)} features) ===")
    model = lgb.LGBMRegressor(**params)
    metrics = evaluate(model, X, y, "LightGBM")

    final_model = lgb.LGBMRegressor(**params)
    final_model.fit(X, y)

    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    final_model.booster_.save_model(str(ARTIFACTS / model_filename))

    importance = pd.Series(
        final_model.booster_.feature_importance(importance_type="gain"),
        index=feature_cols,
    ).sort_values(ascending=False)
    print(f"  Top features (gain):")
    for feat, imp in importance.head(8).items():
        print(f"    {feat}: {imp:.0f}")

    return metrics, feature_cols, importance


def main():
    df = pd.read_csv(DATA_PROCESSED / "players_features.csv")
    reliable = df[df["meets_minutes_threshold"]]

    groups = modelling_groups(reliable)
    outfield, keepers = groups["outfield"], groups["goalkeepers"]

    of_metrics, of_features, of_importance = run_group(
        outfield, OUTFIELD_FEATURES, OUTFIELD_PARAMS, "Outfield players", "outfield_model.txt"
    )
    gk_metrics, gk_features, gk_importance = run_group(
        keepers, GOALKEEPER_FEATURES, GOALKEEPER_PARAMS, "Goalkeepers", "keeper_model.txt"
    )

    baseline = json.loads((ARTIFACTS / "baseline_metrics.json").read_text())
    print("\n=== LightGBM vs. linear regression baseline (EUR R2) ===")
    print(f"  Outfield:    baseline={baseline['outfield']['linear_regression']['r2_eur']:.3f}"
          f"   LightGBM={of_metrics['r2_eur']:.3f}")
    print(f"  Goalkeepers: baseline={baseline['goalkeepers']['linear_regression']['r2_eur']:.3f}"
          f"   LightGBM={gk_metrics['r2_eur']:.3f}")

    (ARTIFACTS / "lightgbm_metrics.json").write_text(json.dumps(
        {"outfield": of_metrics, "goalkeepers": gk_metrics}, indent=2
    ))
    (ARTIFACTS / "outfield_features.json").write_text(json.dumps(of_features, indent=2))
    (ARTIFACTS / "keeper_features.json").write_text(json.dumps(gk_features, indent=2))
    of_importance.to_json(ARTIFACTS / "outfield_feature_importance.json", indent=2)
    gk_importance.to_json(ARTIFACTS / "keeper_feature_importance.json", indent=2)
    print(f"\nSaved models and metrics to {ARTIFACTS}")


if __name__ == "__main__":
    main()
