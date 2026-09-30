"""Cross-fitted transfer screening, with nested model selection and error margins.

Each outer fold selects a model using only its training players. Inner held-out
errors set a conservative log-value margin; this is an empirical screening
buffer, not a guaranteed confidence interval or a future transfer prediction.
Fold models are saved so API explanations describe the exact displayed estimate.
"""
import json
import sys
from pathlib import Path

import joblib
import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Ridge
from sklearn.metrics import r2_score, mean_absolute_error
from sklearn.model_selection import KFold, cross_val_predict
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.utils.features import OUTFIELD_FEATURES, GOALKEEPER_FEATURES, modelling_groups
from app.utils.model_features import build_matrix
from app.utils.bargains import assess_bargain, performance_scores
from train_lightgbm import OUTFIELD_PARAMS, GOALKEEPER_PARAMS

ROOT = Path(__file__).resolve().parent.parent
ARTIFACTS = ROOT / "model" / "artifacts"


def candidate_models(group):
    params = OUTFIELD_PARAMS if group == "outfield" else GOALKEEPER_PARAMS
    return {
        "lightgbm": lgb.LGBMRegressor(**params, n_jobs=2),
        "regularized_lightgbm": lgb.LGBMRegressor(**{
            **params, "num_leaves": 7, "max_depth": 3, "min_child_samples": 30,
            "reg_lambda": 5.0, "reg_alpha": 1.0, "subsample_freq": 1, "n_jobs": 2,
        }),
        "ridge": make_pipeline(SimpleImputer(strategy="median"), StandardScaler(), Ridge(alpha=20)),
    }


def crossfit_group(df, group, artifact_dir):
    cols = list(GOALKEEPER_FEATURES if group == "goalkeepers" else OUTFIELD_FEATURES)
    if group == "outfield":
        cols += [f"pos_{p}" for p in sorted(df.position_group.unique())]
    X = build_matrix(df, cols)
    y = df.log_market_value
    output = pd.DataFrame(index=df.index)
    folds = []
    for fold, (train, test) in enumerate(KFold(5, shuffle=True, random_state=42).split(X)):
        inner = KFold(4, shuffle=True, random_state=100 + fold)
        models = candidate_models(group)
        predictions = {name: cross_val_predict(model, X.iloc[train], y.iloc[train], cv=inner)
                       for name, model in models.items()}
        # Select on log MAE: proportionate error, less driven by superstar prices.
        errors = {name: mean_absolute_error(y.iloc[train], pred) for name, pred in predictions.items()}
        chosen = min(errors, key=errors.get)
        residuals = predictions[chosen] - y.iloc[train].to_numpy()
        # Calibrate to the target market using training PL players only.
        residuals = residuals[df.iloc[train].is_premier_league.to_numpy()]
        margin = max(0.0, float(np.quantile(residuals, 0.8, method="higher")))
        model = models[chosen].fit(X.iloc[train], y.iloc[train])
        pred = model.predict(X.iloc[test])
        idx = df.index[test]
        output.loc[idx, "estimated_market_value_eur"] = np.maximum(0, np.expm1(pred))
        output.loc[idx, "conservative_value_eur"] = np.maximum(0, np.expm1(pred - margin))
        output.loc[idx, "model_fold"] = fold
        prefix = f"{group}_fold_{fold}"
        if "lightgbm" in chosen:
            model.booster_.save_model(str(artifact_dir / f"{prefix}.txt"))
            method = "lightgbm"
        else:
            joblib.dump(model, artifact_dir / f"{prefix}.joblib")
            method = "ridge"
        metadata = {"method": method, "features": cols, "margin_log": margin,
                    "selected_candidate": chosen, "inner_mae_log": errors,
                    "train_player_ids": df.iloc[train].player_id.astype(int).tolist(),
                    "held_out_player_ids": df.iloc[test].player_id.astype(int).tolist()}
        (artifact_dir / f"{prefix}.json").write_text(json.dumps(metadata, indent=2))
        folds.append({k: metadata[k] for k in ("selected_candidate", "margin_log", "inner_mae_log")})
    actual = df.market_value_in_eur
    metrics = {"n": len(df), "r2_eur": r2_score(actual, output.estimated_market_value_eur),
               "mae_eur": mean_absolute_error(actual, output.estimated_market_value_eur),
               "empirical_lower_coverage": float((actual >= output.conservative_value_eur).mean()),
               "folds": folds}
    pl_mask = df.is_premier_league
    metrics["premier_league"] = {
        "n": int(pl_mask.sum()),
        "r2_eur": r2_score(actual[pl_mask], output.loc[pl_mask, "estimated_market_value_eur"]),
        "mae_eur": mean_absolute_error(actual[pl_mask], output.loc[pl_mask, "estimated_market_value_eur"]),
        "empirical_lower_coverage": float((actual[pl_mask] >= output.loc[pl_mask, "conservative_value_eur"]).mean()),
    }
    return output, metrics


def main():
    df = pd.read_csv(ROOT / "data/processed/players_features.csv")
    reliable = df[df.meets_minutes_threshold].copy()
    assert reliable.player_id.is_unique, "One row per identity is required for leakage-free folds"
    metrics = {}
    for group, members in modelling_groups(reliable).items():
        predictions, metrics[group] = crossfit_group(members, group, ARTIFACTS)
        for col in predictions:
            reliable.loc[predictions.index, col] = predictions[col]
        reliable.loc[members.index, "model_supported"] = metrics[group]["premier_league"]["r2_eur"] > 0
        print(group, {k: v for k, v in metrics[group].items() if k != "folds"}, flush=True)
    pl = reliable[reliable.is_premier_league].copy()
    pl["performance_percentile"] = performance_scores(pl)
    pl["value_gap_eur"] = pl.estimated_market_value_eur - pl.market_value_in_eur
    pl["value_gap_pct"] = 100 * pl.value_gap_eur / pl.market_value_in_eur
    pl["conservative_gap_eur"] = pl.conservative_value_eur - pl.market_value_in_eur
    pl["ranking_status"] = pl.apply(assess_bargain, axis=1)
    pl["eligible_for_ranking"] = pl.ranking_status == "Passes screening"
    cols = ["player_id", "Player", "Squad", "position_group", "Age", "Min", "market_value_in_eur",
            "estimated_market_value_eur", "value_gap_eur", "value_gap_pct", "conservative_value_eur",
            "conservative_gap_eur", "performance_percentile", "model_fold", "ranking_status", "eligible_for_ranking"]
    pl[cols].sort_values(["eligible_for_ranking", "conservative_gap_eur"], ascending=False).to_csv(ARTIFACTS / "rankings.csv", index=False)
    metrics["methodology"] = {"version": "bargain-screen-v4", "season": "2025-26",
        "prediction": "Nested 5-fold held-out estimates; model selection on inner 4-fold log MAE",
        "buffer": "80th percentile of training PL inner held-out log overprediction; empirical, not guaranteed coverage",
        "min_minutes": 1800, "min_value_eur": 1000000, "min_performance_percentile": 50,
        "default_sort": "conservative_gap_eur", "valuation_date_max": str(df.valuation_date.max()),
        # Provenance and freshness of every input, shown on the dashboard.
        "data_sources": [
            {"name": "FBref", "scope": "Big-5 leagues, 2025-26", "coverage": "Full season",
             "used_for": "Minutes, club strength, goalkeeper stats, identity"},
            {"name": "SofaScore (Kaggle export)", "scope": "Premier League, 2025-26",
             "coverage": "Through matchday 35 of 38",
             "used_for": "Outfield model, production check, radar, similar players"},
            {"name": "Fantasy Premier League (vaastav community archive)", "scope": "Premier League, 2025-26",
             "coverage": "Full season", "used_for": "Outfield model, birth-date identity checks"},
            {"name": "Transfermarkt (dcaribou dataset)", "scope": "Market valuations",
             "coverage": f"Latest valuation {df.valuation_date.max()}; dataset updates paused",
             "used_for": "Target the model learns to estimate"},
        ]}
    (ARTIFACTS / "screening_metrics.json").write_text(json.dumps(metrics, indent=2))
    print(pl[pl.eligible_for_ranking][["Player", "conservative_gap_eur", "performance_percentile"]].to_string(index=False))

if __name__ == "__main__":
    main()
