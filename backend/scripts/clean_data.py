"""
Cleans the combined training set: resolves cross-league duplicate players,
drops rows with unusable core data, derives a broad position group, and flags
players below the minimum-minutes threshold rather than silently dropping them.

Minimum minutes: 900 (~10 full matches). Below this, per-90 rates are
dominated by small-sample noise (a player with 30 minutes and one goal has an
absurd per-90 goal rate). Players below the threshold are kept in the output
and still shown in the product, but excluded from model training and from the
undervaluation ranking, where a trustworthy per-90 profile matters most.

Usage: python scripts/clean_data.py (run build_training_set.py first)
"""

from pathlib import Path

import pandas as pd

DATA_PROCESSED = Path(__file__).resolve().parent.parent / "data" / "processed"
MIN_MINUTES = 900

# FBref lists multi-position players as e.g. "MF,FW"; the first tag is their
# primary listed role, which is what we group by for position-relative analysis.
POSITION_GROUPS = {"GK": "GK", "DF": "DF", "MF": "MF", "FW": "FW"}


def resolve_cross_league_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """A player who transferred between two of the Big 5 leagues mid-season
    ends up with one row per league (they're different Comp values, so
    merge_transfer_rows doesn't catch this). Keep one row per player_id:
    prefer their Premier League row if they have one, otherwise the row
    where they played more minutes.

    Sorting + drop_duplicates (rather than groupby().apply()) is used
    deliberately: pandas silently drops the groupby key from the result when
    the applied function returns a Series per group, which would lose
    player_id here."""
    df = df.sort_values(["is_premier_league", "Min"], ascending=[False, False])
    return df.drop_duplicates(subset="player_id", keep="first").reset_index(drop=True)


def derive_position_group(pos: str) -> str:
    primary = pos.split(",")[0]
    return POSITION_GROUPS.get(primary, primary)


def main():
    df = pd.read_csv(DATA_PROCESSED / "training_set_raw.csv")
    n_start = len(df)

    n_missing_age = df["Age"].isnull().sum()
    df = df.dropna(subset=["Age"])

    n_before_dedup = len(df)
    df = resolve_cross_league_duplicates(df)
    n_after_dedup = len(df)

    # Deterministic row order so downstream shuffled CV splits (fixed random_state,
    # but seeded relative to row position) are reproducible across reruns.
    df = df.sort_values("player_id").reset_index(drop=True)

    df["position_group"] = df["Pos"].apply(derive_position_group)
    df["meets_minutes_threshold"] = df["Min"] >= MIN_MINUTES

    df.to_csv(DATA_PROCESSED / "players_clean.csv", index=False)

    print(f"Start: {n_start} rows")
    print(f"Dropped {n_missing_age} row(s) with missing Age")
    print(f"Resolved {n_before_dedup - n_after_dedup} cross-league duplicate player(s)")
    print(f"Final clean dataset: {n_after_dedup} players")
    print(f"  meets {MIN_MINUTES}-minute threshold: {df['meets_minutes_threshold'].sum()}")
    print(f"  below threshold (kept, flagged): {(~df['meets_minutes_threshold']).sum()}")
    print()
    print("Position group counts:")
    print(df["position_group"].value_counts())
    print()
    print("Premier League players in clean set:", df["is_premier_league"].sum())
    print("  of which meet minutes threshold:",
          df[df["is_premier_league"]]["meets_minutes_threshold"].sum())


if __name__ == "__main__":
    main()
