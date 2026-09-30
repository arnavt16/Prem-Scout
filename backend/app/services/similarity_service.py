"""Stylistically similar players within the same position group.

Per-90 style stats are robust-scaled against reliable-minutes Premier League
peers (median/IQR, so one extreme outlier doesn't define the scale) and
compared with cosine similarity, which matches the *shape* of a profile rather
than its overall volume. Context such as age, club strength or price is left
out on purpose: the question is "who plays like this?", and the value columns
returned alongside let a scout compare prices afterwards.
"""

from functools import lru_cache

import numpy as np
import pandas as pd

from app.services import data_store
from app.utils.model_features import feature_label

STYLE_FEATURES = {
    "outfield": ["ss_expectedGoals_p90", "ss_expectedAssists_p90", "ss_totalShots_p90", "ss_keyPasses_p90",
                 "ss_successfulDribbles_p90", "ss_accurateFinalThirdPasses_p90", "ss_accurateLongBalls_p90",
                 "ss_touches_p90", "ss_tacklesWon_p90", "ss_interceptions_p90", "ss_clearances_p90",
                 "ss_aerialDuelsWon_p90", "ss_ballRecovery_p90"],
    "GK": ["GA90", "Save%", "CS%"],
}
# A trait is only "shared" when both players sit at least this many IQRs
# above the peer median. Shared *absences* (e.g. both rarely draw fouls) are
# real similarity but read as noise when shown to a person.
TRAIT_THRESHOLD = 0.5
MAX_TRAITS = 3


def _style_group(position_group: str) -> str:
    return "GK" if position_group == "GK" else "outfield"


@lru_cache(maxsize=4)
def _scaled_peers(position_group: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    players = data_store.load_players()
    peers = players[(players["position_group"] == position_group)
                    & players["meets_minutes_threshold"]].reset_index(drop=True)
    cols = STYLE_FEATURES[_style_group(position_group)]
    stats = peers[cols].astype(float)
    median = stats.median()
    iqr = (stats.quantile(0.75) - stats.quantile(0.25)).replace(0, 1)
    # Missing rates (rare) sit at the peer median, i.e. contribute nothing.
    scaled = ((stats - median) / iqr).fillna(0)
    return peers, scaled


def _shared_traits(a: pd.Series, b: pd.Series) -> list[str]:
    both_high = (a >= TRAIT_THRESHOLD) & (b >= TRAIT_THRESHOLD)
    strength = (a * b)[both_high].sort_values(ascending=False)
    return [feature_label(col) for col in strength.index[:MAX_TRAITS]]


def similar_players(player_id: int, limit: int = 5) -> list[dict] | None:
    players = data_store.load_players()
    match = players[players["player_id"] == player_id]
    if match.empty or not match.iloc[0]["meets_minutes_threshold"]:
        return None

    peers, scaled = _scaled_peers(match.iloc[0]["position_group"])
    target_idx = peers.index[peers["player_id"] == player_id][0]
    target = scaled.loc[target_idx]

    norms = np.linalg.norm(scaled.to_numpy(), axis=1) * np.linalg.norm(target.to_numpy())
    similarity = pd.Series(scaled.to_numpy() @ target.to_numpy() / np.where(norms == 0, 1, norms),
                           index=scaled.index).drop(target_idx)

    results = []
    for idx, score in similarity.nlargest(limit).items():
        row = peers.loc[idx]
        results.append({
            "player_id": int(row["player_id"]),
            "name": row.get("matched_name", row["Player"]),
            "club": row["Squad"],
            "sub_position": row["sub_position"],
            "age": row["Age"],
            "market_value_eur": int(row["market_value_in_eur"]),
            "estimated_market_value_eur": None if pd.isna(row["estimated_market_value_eur"])
                                          else float(row["estimated_market_value_eur"]),
            "similarity": round(float(score), 3),
            "shared_traits": _shared_traits(target, scaled.loc[idx]),
        })
    return results
