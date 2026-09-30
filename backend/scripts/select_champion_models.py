"""
Picks the production model per position group by comparing the LightGBM and
linear-regression cross-validated EUR-space R2 (both already computed by
train_baseline.py and train_lightgbm.py). This is not a formality: for
goalkeepers, linear regression outperforms LightGBM (see model_selection.json
after running this), because 113 rows and 6 features give a boosted tree
model more capacity to overfit than signal to find. Outfield keeps LightGBM,
which does win there.

The losing model isn't deleted. Both stay in model/artifacts/ so the
comparison remains checkable, but only the winner is written as the
*_production.* file the API loads.

Usage: python scripts/select_champion_models.py (run train_baseline.py and
train_lightgbm.py first)
"""

import json
from pathlib import Path

import joblib
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.pipeline import Pipeline

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.utils.features import OUTFIELD_FEATURES, GOALKEEPER_FEATURES, modelling_groups  # noqa: E402

DATA_PROCESSED = Path(__file__).resolve().parent.parent / "data" / "processed"
ARTIFACTS = Path(__file__).resolve().parent.parent / "model" / "artifacts"


def build_matrix(df, feature_cols):
    df = df.copy()
    if df["position_group"].nunique() > 1:
        dummies = pd.get_dummies(df["position_group"], prefix="pos")
        df = pd.concat([df, dummies], axis=1)
        feature_cols = feature_cols + list(dummies.columns)
    return df[feature_cols], df["log_market_value"], feature_cols


def main():
    baseline = json.loads((ARTIFACTS / "baseline_metrics.json").read_text())
    lightgbm = json.loads((ARTIFACTS / "lightgbm_metrics.json").read_text())

    df = pd.read_csv(DATA_PROCESSED / "players_features.csv")
    reliable = df[df["meets_minutes_threshold"]]
    groups = {
        "outfield": (modelling_groups(reliable)["outfield"], OUTFIELD_FEATURES),
        "goalkeepers": (modelling_groups(reliable)["goalkeepers"], GOALKEEPER_FEATURES),
    }

    selection = {}
    for group, (group_df, feature_cols) in groups.items():
        lgb_r2 = lightgbm[group]["r2_eur"]
        lin_r2 = baseline[group]["linear_regression"]["r2_eur"]
        winner = "lightgbm" if lgb_r2 >= lin_r2 else "linear_regression"
        selection[group] = {"lightgbm_r2_eur": lgb_r2, "linear_regression_r2_eur": lin_r2,
                             "chosen_model": winner}
        print(f"{group}: lightgbm R2={lgb_r2:.3f}  linear_regression R2={lin_r2:.3f}  "
              f"-> using {winner}")

        if winner == "linear_regression":
            X, y, used_cols = build_matrix(group_df, feature_cols)
            model = Pipeline([
                ("impute", SimpleImputer(strategy="median")),
                ("model", LinearRegression()),
            ])
            model.fit(X, y)
            joblib.dump(model, ARTIFACTS / f"{group}_production.joblib")
            (ARTIFACTS / f"{group}_production_features.json").write_text(
                json.dumps(used_cols, indent=2)
            )
        # LightGBM winners were already saved as outfield_model.txt / keeper_model.txt
        # by train_lightgbm.py; nothing further to do for that case.

    (ARTIFACTS / "model_selection.json").write_text(json.dumps(selection, indent=2))
    print(f"\nSaved selection record to {ARTIFACTS / 'model_selection.json'}")


if __name__ == "__main__":
    main()
