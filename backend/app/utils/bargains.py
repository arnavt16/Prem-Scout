"""Transparent shortlist rules; no player names or reputation overrides."""
import numpy as np
import pandas as pd

# Position-relative production from SofaScore event stats, independent of
# price. Each role mixes SofaScore's match rating with the actions that define
# it; defenders also get passing volume so the check doesn't only reward
# defenders on teams that spend the game without the ball. Not an overall
# talent rating: injuries, wages and contract length are not in the data.
PERFORMANCE_STATS = {
    "DF": ["ss_rating", "ss_tacklesWon_p90", "ss_interceptions_p90", "ss_aerialDuelsWon_p90",
           "ss_accuratePasses_p90", "ss_groundDuelsWonPercentage"],
    "MF": ["ss_rating", "ss_expectedAssists_p90", "ss_keyPasses_p90", "ss_accurateFinalThirdPasses_p90",
           "ss_successfulDribbles_p90", "ss_ballRecovery_p90", "ss_tacklesWon_p90"],
    "FW": ["ss_rating", "ss_expectedGoals_p90", "ss_goals_p90", "ss_expectedAssists_p90",
           "ss_keyPasses_p90", "ss_successfulDribbles_p90"],
}


def performance_scores(df):
    result = pd.Series(np.nan, index=df.index)
    for position, stats in PERFORMANCE_STATS.items():
        peers = df[df.position_group == position]
        if peers.empty:
            continue
        # Shrink noisy per-90 rates toward the position median by 900 minutes.
        weight = peers.Min / (peers.Min + 900)
        adjusted = peers[stats].mul(weight, axis=0) + pd.DataFrame(
            np.outer(1 - weight, peers[stats].median()), index=peers.index, columns=stats)
        composite = adjusted.rank(pct=True).mean(axis=1)
        result.loc[peers.index] = composite.rank(pct=True) * 100
    return result


def assess_bargain(row):
    if not row.get("identity_verified", False):
        return "Identity unverified"
    if row["Min"] < 1800:
        return "Needs 1,800 minutes"
    if row["market_value_in_eur"] < 1_000_000:
        return "Below €1M value floor"
    if not row["model_supported"] or row["position_group"] == "GK":
        return "Model evidence too weak"
    if pd.isna(row["performance_percentile"]) or row["performance_percentile"] < 50:
        return "Below performance screen"
    if not np.isfinite(row["conservative_gap_eur"]) or row["conservative_gap_eur"] <= 0:
        return "Gap within model uncertainty"
    return "Passes screening"
