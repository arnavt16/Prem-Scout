import numpy as np
import pandas as pd

# Raw counting stats that get converted to a per-90 rate. Per-90 is used
# instead of raw totals so a player who's played more minutes isn't rewarded
# purely for accumulation.
OUTFIELD_COUNTING_STATS = [
    "Gls", "Ast", "Sh", "SoT", "Crs", "Int", "TklW", "CrdY", "CrdR", "Fls", "Fld", "Off",
]

# Big-5 competitions as FBref labels them. One flag per non-PL league (the PL
# flag already exists) lets the model learn each market's price level.
LEAGUES = {
    "league_bundesliga": "de Bundesliga", "league_la_liga": "es La Liga",
    "league_ligue_1": "fr Ligue 1", "league_serie_a": "it Serie A",
}

# Market context shared by both models. team_ppm measures the strength of the
# player's club from this season's results (not reputation or club identity):
# the market prices a starter at a title contender above an equivalent
# producer at a relegation side. Age_sq lets the linear candidate model a
# peak-age curve instead of a straight line.
CONTEXT_FEATURES = ["Age", "Age_sq", "Min", "team_ppm", "is_premier_league", *LEAGUES]

# Goalkeeper stats FBref already provides as rates (GA90, Save%, CS%) or as
# meaningful raw counts over a season (PKsv, PKA, PKm), so no per-90 conversion is needed.
GOALKEEPER_FEATURES = ["GA90", "Save%", "CS%", "PKsv", "PKA", "PKm", *CONTEXT_FEATURES]

# SofaScore event stats (Premier League only, through matchday 35 of 38).
# Counting stats become per-90 rates over SofaScore's own minutes, so the
# numerator and denominator come from the same provider and period.
SOFASCORE_COUNTING_STATS = [
    "expectedGoals", "expectedAssists", "keyPasses", "bigChancesCreated", "successfulDribbles",
    "accurateFinalThirdPasses", "accurateOppositionHalfPasses", "accuratePasses", "accurateLongBalls",
    "touches", "ballRecovery", "possessionWonAttThird", "tacklesWon", "interceptions", "clearances",
    "aerialDuelsWon", "groundDuelsWon", "dispossessed", "possessionLost", "dribbledPast", "wasFouled",
    "shotsFromInsideTheBox", "totalShots", "goals", "outfielderBlocks", "errorLeadToShot", "totwAppearances",
]
SOFASCORE_RATES = [
    "accuratePassesPercentage", "aerialDuelsWonPercentage", "groundDuelsWonPercentage",
    "successfulDribblesPercentage", "rating",
]
SOFASCORE_FEATURES = (
    [f"ss_{c}_p90" for c in SOFASCORE_COUNTING_STATS]
    + [f"ss_{c}" for c in SOFASCORE_RATES]
    + ["ss_np_goals_minus_xg_p90", "ss_start_share"]
)

# Fantasy Premier League season stats (full 38 matchdays). ICT components and
# bonus points are FPL's own composite scores; expected goals conceded and
# clean sheets capture defensive record while a player was on the pitch.
FPL_STATS = [
    "influence", "creativity", "threat", "bps", "defensive_contribution", "recoveries", "tackles",
    "clearances_blocks_interceptions", "expected_goals_conceded", "goals_conceded", "clean_sheets",
    "expected_goals", "expected_assists",
]
FPL_FEATURES = [f"fpl_{c}_p90" for c in FPL_STATS] + ["fpl_start_share"]

# The outfield model trains on Premier League players only: in nested CV it
# beat the Big-5 model on PL players even with the same FBref stats (R² 0.698
# vs 0.643), and SofaScore's richer stats exist only for the PL. League flags
# are constant within one league, so only age, minutes and club strength remain.
# FPL features cut held-out average error by about €0.3M in each of five
# different fold splits on top of SofaScore.
OUTFIELD_FEATURES = [*SOFASCORE_FEATURES, *FPL_FEATURES, "Age", "Age_sq", "Min", "team_ppm"]
CONTEXT_COLUMNS = ["player_id", "Player", "Squad", "Comp", "position_group",
                   "sub_position", "Age", "Min", "is_premier_league", "is_premier_league", "meets_minutes_threshold"]


def modelling_groups(reliable: pd.DataFrame) -> dict[str, pd.DataFrame]:
    """Training populations: PL outfield players (see OUTFIELD_FEATURES) and
    Big-5 goalkeepers, since 24 PL keepers are too few to train on alone."""
    is_gk = reliable["position_group"] == "GK"
    return {
        "outfield": reliable[~is_gk & reliable["is_premier_league"]],
        "goalkeepers": reliable[is_gk],
    }


def add_sofascore_features(df: pd.DataFrame, sofascore: pd.DataFrame) -> pd.DataFrame:
    """Left-joins SofaScore-derived features on player_id; players without a
    confident SofaScore match (non-PL, or unmatched) get NaN."""
    ss = sofascore.set_index("player_id")
    nineties = ss["ss_minutesPlayed"] / 90
    feats = pd.DataFrame(index=ss.index)
    for col in SOFASCORE_COUNTING_STATS:
        feats[f"ss_{col}_p90"] = ss[f"ss_{col}"] / nineties
    for col in SOFASCORE_RATES:
        feats[f"ss_{col}"] = ss[f"ss_{col}"]
    feats["ss_np_goals_minus_xg_p90"] = (
        ss["ss_goals"] - ss["ss_penaltyGoals"] - ss["ss_expectedGoals"]) / nineties
    feats["ss_start_share"] = ss["ss_matchesStarted"] / ss["ss_appearances"].replace(0, np.nan)
    # A few raw totals are shown on profiles as-is.
    for col in ["expectedGoals", "expectedAssists", "keyPasses", "bigChancesCreated",
                "successfulDribbles", "minutesPlayed"]:
        feats[f"ss_{col}"] = ss[f"ss_{col}"]
    feats = feats.replace([np.inf, -np.inf], np.nan)
    return df.drop(columns=[c for c in feats.columns if c in df.columns]).join(feats, on="player_id")


def add_fpl_features(df: pd.DataFrame, fpl: pd.DataFrame) -> pd.DataFrame:
    """Left-joins FPL-derived per-90 features on player_id."""
    fpl = fpl.set_index("player_id")
    nineties = (fpl["fpl_minutes"] / 90).replace(0, np.nan)
    feats = pd.DataFrame(index=fpl.index)
    for col in FPL_STATS:
        feats[f"fpl_{col}_p90"] = pd.to_numeric(fpl[f"fpl_{col}"], errors="coerce") / nineties
    feats["fpl_start_share"] = fpl["fpl_starts"] / 38
    return df.drop(columns=[c for c in feats.columns if c in df.columns]).join(feats, on="player_id")


def engineer_features(df: pd.DataFrame, sofascore: pd.DataFrame | None = None,
                      fpl: pd.DataFrame | None = None) -> pd.DataFrame:
    df = df.copy()
    nineties = df["Min"] / 90

    for col in OUTFIELD_COUNTING_STATS:
        df[f"{col}_per90"] = df[col] / nineties

    # SoT%, G/Sh, G/SoT are already rates from FBref but divide by zero when a
    # player has taken no shots. That's a legitimate 0-shot player, not
    # missing data, so it's left as NaN and LightGBM splits around it natively.
    for col in ["SoT%", "G/Sh", "G/SoT"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["Age_sq"] = (df["Age"] - 25) ** 2
    for col, comp in LEAGUES.items():
        df[col] = (df["Comp"] == comp).astype(int)

    # Minutes-weighted points per match across every squad member, including
    # those below the modelling minutes threshold, so it reflects the club.
    weighted = (df["PPM"] * df["Min"]).groupby([df["Squad"], df["Comp"]]).sum()
    team_ppm = weighted / df.groupby(["Squad", "Comp"])["Min"].sum()
    df["team_ppm"] = pd.MultiIndex.from_frame(df[["Squad", "Comp"]]).map(team_ppm)

    if sofascore is not None:
        df = add_sofascore_features(df, sofascore)
    if fpl is not None:
        df = add_fpl_features(df, fpl)

    if "market_value_in_eur" in df.columns:
        df["log_market_value"] = np.log1p(df["market_value_in_eur"])

    return df
