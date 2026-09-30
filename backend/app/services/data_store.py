"""
Loads the processed dataset and model artifacts once at import time and
exposes them as plain pandas/dict objects. Kept free of FastAPI so it can be
tested and reasoned about independently of the web layer.
"""

import json
from pathlib import Path
from functools import lru_cache

import pandas as pd

DATA_PROCESSED = Path(__file__).resolve().parent.parent.parent / "data" / "processed"
ARTIFACTS = Path(__file__).resolve().parent.parent.parent / "model" / "artifacts"

RANKING_COLUMNS = [
    "player_id", "estimated_market_value_eur", "value_gap_eur",
    "value_gap_pct", "eligible_for_ranking", "conservative_value_eur",
    "conservative_gap_eur", "performance_percentile", "ranking_status", "model_fold",
]


@lru_cache
def load_players() -> pd.DataFrame:
    """The matched Premier League universe with held-out valuation estimates
    left-joined for players who meet the estimation minutes threshold.
    Players below the threshold still appear, with those fields as null,
    rather than being silently excluded from the product."""
    features = pd.read_csv(DATA_PROCESSED / "players_features.csv")
    pl = features[features["is_premier_league"]].copy()

    rankings = pd.read_csv(ARTIFACTS / "rankings.csv")[RANKING_COLUMNS]
    merged = pl.merge(rankings, on="player_id", how="left")
    merged["eligible_for_ranking"] = (
        merged["eligible_for_ranking"].fillna(False).infer_objects(copy=False).astype(bool)
    )
    merged["ranking_status"] = merged["ranking_status"].fillna("Needs 900 minutes for estimate")
    return merged


@lru_cache
def load_model_metrics() -> dict:
    return {
        "screening": json.loads((ARTIFACTS / "screening_metrics.json").read_text()),
        "baseline": json.loads((ARTIFACTS / "baseline_metrics.json").read_text()),
        "lightgbm": json.loads((ARTIFACTS / "lightgbm_metrics.json").read_text()),
        "model_selection": json.loads((ARTIFACTS / "model_selection.json").read_text()),
        "transfer_validation": json.loads((ARTIFACTS / "transfer_validation.json").read_text()),
    }
