import pandas as pd

from app.schemas.player import ModelMetrics, PlayerDetail, PlayerSummary
from app.services import data_store
from app.utils.radar import compute_percentiles, radar_labels

SORTABLE_FIELDS = {
    "conservative_gap_eur": "conservative_gap_eur",
    "performance_percentile": "performance_percentile",
    "value_gap_eur": "value_gap_eur",
    "value_gap_pct": "value_gap_pct",
    "estimated_market_value_eur": "estimated_market_value_eur",
    "market_value_eur": "market_value_in_eur",
    "goals": "Gls",
    "assists": "Ast",
    "minutes": "Min",
    "age": "Age",
    "rating": "ss_rating",
    "xg": "ss_expectedGoals",
    "xa": "ss_expectedAssists",
}


def _n(value):
    """None for NaN, otherwise the value. Pandas NaN isn't valid for a
    Pydantic Optional[float] field."""
    return None if pd.isna(value) else value


def _round(value, digits):
    return None if pd.isna(value) else round(float(value), digits)


def _int(value):
    return None if pd.isna(value) else int(value)


def _to_summary(row: pd.Series) -> PlayerSummary:
    return PlayerSummary(
        player_id=int(row["player_id"]),
        name=row.get("matched_name", row["Player"]),
        club=row["Squad"],
        position_group=row["position_group"],
        sub_position=row["sub_position"],
        age=row["Age"],
        minutes=int(row["Min"]),
        goals=int(row["Gls"]),
        assists=int(row["Ast"]),
        market_value_eur=int(row["market_value_in_eur"]),
        estimated_market_value_eur=_n(row["estimated_market_value_eur"]),
        value_gap_eur=_n(row["value_gap_eur"]),
        value_gap_pct=_n(row["value_gap_pct"]),
        conservative_value_eur=_n(row["conservative_value_eur"]),
        conservative_gap_eur=_n(row["conservative_gap_eur"]),
        performance_percentile=_n(row["performance_percentile"]),
        ranking_status=row["ranking_status"],
        valuation_date=str(row["valuation_date"]),
        meets_minutes_threshold=bool(row["meets_minutes_threshold"]),
        eligible_for_ranking=bool(row["eligible_for_ranking"]),
        rating=_round(row.get("ss_rating"), 2),
        xg=_round(row.get("ss_expectedGoals"), 2),
        xa=_round(row.get("ss_expectedAssists"), 2),
    )


def _to_radar(row: pd.Series) -> list[dict]:
    peers = data_store.load_players()
    peers = peers[
        (peers["position_group"] == row["position_group"]) & (peers["meets_minutes_threshold"])
    ]
    percentiles = compute_percentiles(row, peers)
    labels = {c["key"]: c["label"] for c in radar_labels(row["position_group"])}
    return [
        {"key": key, "label": labels[key], "percentile": pct}
        for key, pct in percentiles.items()
    ]


def _to_detail(row: pd.Series) -> PlayerDetail:
    is_gk = row["position_group"] == "GK"
    return PlayerDetail(
        **_to_summary(row).model_dump(),
        starts=int(row["Starts"]),
        nineties=row["90s"],
        shots=int(row["Sh"]),
        shots_on_target=int(row["SoT"]),
        shot_on_target_pct=_n(row["SoT%"]),
        goals_per_shot=_n(row["G/Sh"]),
        goals_per_shot_on_target=_n(row["G/SoT"]),
        yellow_cards=int(row["CrdY"]),
        red_cards=int(row["CrdR"]),
        goals_per90=row["Gls_per90"],
        assists_per90=row["Ast_per90"],
        shots_per90=row["Sh_per90"],
        shots_on_target_per90=row["SoT_per90"],
        crosses_per90=row["Crs_per90"],
        interceptions_per90=row["Int_per90"],
        tackles_won_per90=row["TklW_per90"],
        fouls_committed_per90=row["Fls_per90"],
        fouls_drawn_per90=row["Fld_per90"],
        offsides_per90=row["Off_per90"],
        yellow_cards_per90=row["CrdY_per90"],
        red_cards_per90=row["CrdR_per90"],
        key_passes=_int(row.get("ss_keyPasses")),
        big_chances_created=_int(row.get("ss_bigChancesCreated")),
        successful_dribbles=_int(row.get("ss_successfulDribbles")),
        xg_per90=_round(row.get("ss_expectedGoals_p90"), 3),
        xa_per90=_round(row.get("ss_expectedAssists_p90"), 3),
        key_passes_per90=_round(row.get("ss_keyPasses_p90"), 3),
        dribbles_per90=_round(row.get("ss_successfulDribbles_p90"), 3),
        final_third_passes_per90=_round(row.get("ss_accurateFinalThirdPasses_p90"), 3),
        pass_completion_pct=_round(row.get("ss_accuratePassesPercentage"), 1),
        aerial_win_pct=_round(row.get("ss_aerialDuelsWonPercentage"), 1),
        sofascore_minutes=_int(row.get("ss_minutesPlayed")),
        goals_against_per90=_n(row["GA90"]) if is_gk else None,
        save_pct=_n(row["Save%"]) if is_gk else None,
        clean_sheet_pct=_n(row["CS%"]) if is_gk else None,
        penalty_saves=int(row["PKsv"]) if is_gk else None,
        penalties_faced=int(row["PKA"]) if is_gk else None,
        penalties_missed=int(row["PKm"]) if is_gk else None,
        radar=_to_radar(row),
    )


def _apply_filters(df, club=None, position=None, min_age=None, max_age=None,
                    min_minutes=None, min_value=None, max_value=None):
    if club:
        df = df[df["Squad"] == club]
    if position:
        df = df[df["position_group"] == position]
    if min_age is not None:
        df = df[df["Age"] >= min_age]
    if max_age is not None:
        df = df[df["Age"] <= max_age]
    if min_minutes is not None:
        df = df[df["Min"] >= min_minutes]
    if min_value is not None:
        df = df[df["market_value_in_eur"] >= min_value]
    if max_value is not None:
        df = df[df["market_value_in_eur"] <= max_value]
    return df


def _apply_sort(df, sort_by, order):
    if not sort_by:
        return df
    column = SORTABLE_FIELDS.get(sort_by)
    if not column:
        return df
    return df.sort_values(column, ascending=(order == "asc"), na_position="last")


def list_players(sort_by=None, order="desc", **filters) -> list[PlayerSummary]:
    df = _apply_filters(data_store.load_players(), **filters)
    df = _apply_sort(df, sort_by, order)
    return [_to_summary(row) for _, row in df.iterrows()]


def get_player(player_id: int) -> PlayerDetail | None:
    df = data_store.load_players()
    match = df[df["player_id"] == player_id]
    if match.empty:
        return None
    return _to_detail(match.iloc[0])


def list_rankings(sort_by="conservative_gap_eur", order="desc", **filters) -> list[PlayerSummary]:
    df = data_store.load_players()
    df = df[df["eligible_for_ranking"]]
    df = _apply_filters(df, **filters)
    df = _apply_sort(df, sort_by, order)
    return [_to_summary(row) for _, row in df.iterrows()]


def list_clubs() -> list[str]:
    return sorted(data_store.load_players()["Squad"].unique().tolist())


def list_positions() -> list[str]:
    return sorted(data_store.load_players()["position_group"].unique().tolist())


def get_model_metrics() -> ModelMetrics:
    return ModelMetrics(**data_store.load_model_metrics())
