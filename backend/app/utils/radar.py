"""
Radar chart categories, one set per broad player type. Outfield categories use
SofaScore event stats. Each category maps to
a per-90 (or already-normalized) column; `invert=True` means a lower raw
value is better (e.g. conceding fewer goals), so the percentile is flipped
before display so "further out on the radar" always means "better."

Percentiles are computed against same-position, reliable-minutes peers only.
Comparing a player's rate stats to a peer with 100 minutes would be
comparing signal to noise.
"""

import pandas as pd

OUTFIELD_RADAR = [
    {"key": "goal_threat", "label": "Goal Threat (xG)", "column": "ss_expectedGoals_p90", "invert": False},
    {"key": "creation", "label": "Chance Creation (xA)", "column": "ss_expectedAssists_p90", "invert": False},
    {"key": "dribbling", "label": "Dribbling", "column": "ss_successfulDribbles_p90", "invert": False},
    {"key": "progression", "label": "Final Third Passing", "column": "ss_accurateFinalThirdPasses_p90", "invert": False},
    {"key": "defense", "label": "Defensive Work", "column": "_defense_score", "invert": False},
    {"key": "aerial", "label": "Aerial Duels", "column": "ss_aerialDuelsWon_p90", "invert": False},
]

GOALKEEPER_RADAR = [
    {"key": "shot_stopping", "label": "Shot Stopping", "column": "Save%", "invert": False},
    {"key": "goals_prevented", "label": "Goals Prevented", "column": "GA90", "invert": True},
    {"key": "clean_sheets", "label": "Clean Sheets", "column": "CS%", "invert": False},
    {"key": "penalty_saving", "label": "Penalty Saves", "column": "PKsv", "invert": False},
]


def _with_derived_columns(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["_defense_score"] = df["ss_tacklesWon_p90"] + df["ss_interceptions_p90"]
    return df


def compute_percentiles(player_row: pd.Series, peer_df: pd.DataFrame) -> dict[str, float]:
    categories = GOALKEEPER_RADAR if player_row["position_group"] == "GK" else OUTFIELD_RADAR
    peers = _with_derived_columns(peer_df)
    player = _with_derived_columns(player_row.to_frame().T).iloc[0]

    percentiles = {}
    for cat in categories:
        values = peers[cat["column"]].dropna()
        value = player[cat["column"]]
        if pd.isna(value) or len(values) == 0:
            percentiles[cat["key"]] = None
            continue
        pct = (values <= value).mean() * 100
        percentiles[cat["key"]] = round(100 - pct if cat["invert"] else pct, 1)

    return percentiles


def radar_labels(position_group: str) -> list[dict]:
    categories = GOALKEEPER_RADAR if position_group == "GK" else OUTFIELD_RADAR
    return [{"key": c["key"], "label": c["label"]} for c in categories]
