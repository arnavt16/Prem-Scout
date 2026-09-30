import pandas as pd

# Human-readable labels for model feature columns, used anywhere a feature
# name needs to be shown to a person rather than matched by code.
FEATURE_LABELS = {
    "Gls_per90": "Goals per 90", "Ast_per90": "Assists per 90",
    "Sh_per90": "Shots per 90", "SoT_per90": "Shots on target per 90",
    "Crs_per90": "Crosses per 90", "Int_per90": "Interceptions per 90",
    "TklW_per90": "Tackles won per 90", "CrdY_per90": "Yellow cards per 90",
    "CrdR_per90": "Red cards per 90", "Fls_per90": "Fouls committed per 90",
    "Fld_per90": "Fouls drawn per 90", "Off_per90": "Offsides per 90",
    "SoT%": "Shot accuracy", "G/Sh": "Goals per shot", "G/SoT": "Goals per shot on target",
    "is_premier_league": "Premier League market context", "Min": "Minutes played", "Age": "Age",
    "Age_sq": "Distance from peak age", "team_ppm": "Club points per match",
    "league_bundesliga": "Bundesliga market context", "league_la_liga": "La Liga market context",
    "league_ligue_1": "Ligue 1 market context", "league_serie_a": "Serie A market context", "GA90": "Goals against per 90", "Save%": "Save percentage",
    "CS%": "Clean sheet percentage", "PKsv": "Penalties saved",
    "PKA": "Penalties faced", "PKm": "Penalties missed",
    "pos_DF": "Position: Defender", "pos_MF": "Position: Midfielder", "pos_FW": "Position: Forward",
}


SOFASCORE_LABELS = {
    "expectedGoals": "xG", "expectedAssists": "xA (expected assists)", "keyPasses": "Key passes",
    "bigChancesCreated": "Big chances created", "successfulDribbles": "Successful dribbles",
    "accurateFinalThirdPasses": "Accurate final third passes",
    "accurateOppositionHalfPasses": "Accurate opposition half passes", "accuratePasses": "Accurate passes",
    "accurateLongBalls": "Accurate long balls", "touches": "Touches", "ballRecovery": "Ball recoveries",
    "possessionWonAttThird": "Possession won in final third", "tacklesWon": "Tackles won",
    "interceptions": "Interceptions", "clearances": "Clearances", "aerialDuelsWon": "Aerial duels won",
    "groundDuelsWon": "Ground duels won", "dispossessed": "Times dispossessed",
    "possessionLost": "Possession lost", "dribbledPast": "Times dribbled past", "wasFouled": "Fouls won",
    "shotsFromInsideTheBox": "Shots inside the box", "totalShots": "Shots", "goals": "Goals",
    "outfielderBlocks": "Blocks", "errorLeadToShot": "Errors leading to a shot",
    "totwAppearances": "Team of the week selections",
}
for _stat, _label in SOFASCORE_LABELS.items():
    FEATURE_LABELS[f"ss_{_stat}_p90"] = f"{_label} per 90"
FEATURE_LABELS.update({
    "ss_accuratePassesPercentage": "Pass completion", "ss_aerialDuelsWonPercentage": "Aerial duel win rate",
    "ss_groundDuelsWonPercentage": "Ground duel win rate", "ss_successfulDribblesPercentage": "Dribble success rate",
    "ss_rating": "SofaScore match rating", "ss_np_goals_minus_xg_p90": "Goals minus xG per 90 (excluding penalties)",
    "ss_start_share": "Share of appearances started",
})
FEATURE_LABELS.update({
    "fpl_influence_p90": "FPL influence per 90", "fpl_creativity_p90": "FPL creativity per 90",
    "fpl_threat_p90": "FPL threat per 90", "fpl_bps_p90": "FPL bonus points system per 90",
    "fpl_defensive_contribution_p90": "FPL defensive contribution per 90",
    "fpl_recoveries_p90": "Recoveries per 90 (FPL)", "fpl_tackles_p90": "Tackles per 90 (FPL)",
    "fpl_clearances_blocks_interceptions_p90": "Clearances, blocks and interceptions per 90",
    "fpl_expected_goals_conceded_p90": "xG conceded while on pitch per 90",
    "fpl_goals_conceded_p90": "Goals conceded while on pitch per 90",
    "fpl_clean_sheets_p90": "Clean sheets per 90", "fpl_expected_goals_p90": "xG per 90 (FPL)",
    "fpl_expected_assists_p90": "xA per 90 (FPL)", "fpl_start_share": "Share of 38 matches started",
})


# Plain-language themes for explaining an estimate to a casual fan. Single
# model inputs can look odd in isolation (being dispossessed often tracks how
# much a player carries the ball), so explanations sum them by theme.
FEATURE_GROUPS = [
    ("Age", ["Age", "Age_sq"]),
    ("Playing time", ["Min", "ss_start_share", "fpl_start_share"]),
    ("Team results", ["team_ppm", "fpl_goals_conceded_p90", "fpl_expected_goals_conceded_p90",
                      "fpl_clean_sheets_p90"]),
    ("Scoring", ["ss_expectedGoals_p90", "ss_goals_p90", "ss_totalShots_p90", "ss_shotsFromInsideTheBox_p90",
                 "ss_np_goals_minus_xg_p90", "fpl_expected_goals_p90", "fpl_threat_p90"]),
    ("Creating chances", ["ss_expectedAssists_p90", "ss_keyPasses_p90", "ss_bigChancesCreated_p90",
                          "fpl_creativity_p90", "fpl_expected_assists_p90"]),
    ("Dribbling & carrying", ["ss_successfulDribbles_p90", "ss_successfulDribblesPercentage", "ss_wasFouled_p90",
                              "ss_dispossessed_p90", "ss_possessionLost_p90"]),
    ("Passing", ["ss_accuratePasses_p90", "ss_accuratePassesPercentage", "ss_accurateFinalThirdPasses_p90",
                 "ss_accurateOppositionHalfPasses_p90", "ss_accurateLongBalls_p90", "ss_touches_p90"]),
    ("Defending", ["ss_tacklesWon_p90", "ss_interceptions_p90", "ss_clearances_p90", "ss_ballRecovery_p90",
                   "ss_possessionWonAttThird_p90", "ss_outfielderBlocks_p90", "ss_dribbledPast_p90",
                   "ss_errorLeadToShot_p90", "fpl_defensive_contribution_p90", "fpl_recoveries_p90",
                   "fpl_tackles_p90", "fpl_clearances_blocks_interceptions_p90"]),
    ("Duels", ["ss_aerialDuelsWon_p90", "ss_groundDuelsWon_p90", "ss_aerialDuelsWonPercentage",
               "ss_groundDuelsWonPercentage"]),
    ("Overall match ratings", ["ss_rating", "ss_totwAppearances_p90", "fpl_influence_p90", "fpl_bps_p90"]),
    ("Goalkeeping", ["GA90", "Save%", "CS%", "PKsv", "PKA", "PKm"]),
    ("Position", ["pos_DF", "pos_MF", "pos_FW"]),
    ("League", ["is_premier_league", "league_bundesliga", "league_la_liga", "league_ligue_1", "league_serie_a"]),
]
_GROUP_OF = {feature: name for name, features in FEATURE_GROUPS for feature in features}


def feature_group(column: str) -> str:
    return _GROUP_OF.get(column, "Other stats")


def feature_label(column: str) -> str:
    return FEATURE_LABELS.get(column, column)


def build_matrix(df: pd.DataFrame, feature_cols: list[str]) -> pd.DataFrame:
    """Builds the exact feature matrix a model expects: adds position one-hot
    columns, then selects/orders columns to match training time. Dummies are
    always computed (not conditioned on more than one position appearing in
    `df`), since a single-row batch trivially has only one position present,
    and skipping dummy creation there would silently zero out that player's
    own position flag. Any column still missing after that (e.g. a position
    category absent from this particular batch) is filled with 0."""
    df = df.copy()
    dummies = pd.get_dummies(df["position_group"], prefix="pos")
    df = pd.concat([df, dummies], axis=1)
    for col in feature_cols:
        if col not in df.columns:
            df[col] = 0
    return df[feature_cols]
