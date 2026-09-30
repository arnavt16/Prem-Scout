"""
Applies the per-90 feature engineering (FBref, plus SofaScore for the PL) to the cleaned dataset and saves the
model-ready feature table.

Usage: python scripts/engineer_features.py (run clean_data.py, match_sofascore.py and match_fpl.py first)
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.utils.features import engineer_features, OUTFIELD_FEATURES, GOALKEEPER_FEATURES  # noqa: E402

DATA_PROCESSED = Path(__file__).resolve().parent.parent / "data" / "processed"


def main():
    df = pd.read_csv(DATA_PROCESSED / "players_clean.csv")
    sofascore = pd.read_csv(DATA_PROCESSED / "sofascore_matched.csv")
    fpl = pd.read_csv(DATA_PROCESSED / "fpl_matched.csv")
    df = engineer_features(df, sofascore, fpl)

    reliable = df[df["meets_minutes_threshold"]]
    outfield = reliable[(reliable["position_group"] != "GK") & reliable["is_premier_league"]]
    keepers = reliable[reliable["position_group"] == "GK"]

    print(f"Total players: {len(df)}, reliable (>=900 min): {len(reliable)}")
    print(f"  outfield: {len(outfield)}, goalkeepers: {len(keepers)}")
    print()

    print("Outfield per-90 feature summary (reliable-minutes players):")
    print(outfield[OUTFIELD_FEATURES].describe().T[["mean", "std", "min", "max"]])
    print()

    print("Goalkeeper feature summary (reliable-minutes players):")
    print(keepers[GOALKEEPER_FEATURES].describe().T[["mean", "std", "min", "max"]])
    print()

    n_inf = np.isinf(outfield[OUTFIELD_FEATURES].select_dtypes(include="number")).sum().sum()
    print(f"Infinite values in outfield features: {n_inf}")

    df.to_csv(DATA_PROCESSED / "players_features.csv", index=False)
    print(f"\nSaved players_features.csv ({len(df)} rows, {len(df.columns)} columns)")


if __name__ == "__main__":
    main()
