from pydantic import BaseModel


class PlayerSummary(BaseModel):
    player_id: int
    name: str
    club: str
    position_group: str
    sub_position: str
    age: float
    minutes: int
    goals: int
    assists: int
    market_value_eur: int
    estimated_market_value_eur: float | None
    value_gap_eur: float | None
    value_gap_pct: float | None
    conservative_value_eur: float | None
    conservative_gap_eur: float | None
    performance_percentile: float | None
    ranking_status: str
    valuation_date: str
    meets_minutes_threshold: bool
    eligible_for_ranking: bool
    # SofaScore season stats (through matchday 35); null without a match.
    rating: float | None
    xg: float | None
    xa: float | None


class PlayerDetail(PlayerSummary):
    starts: int
    nineties: float
    shots: int
    shots_on_target: int
    shot_on_target_pct: float | None
    goals_per_shot: float | None
    goals_per_shot_on_target: float | None
    yellow_cards: int
    red_cards: int

    goals_per90: float
    assists_per90: float
    shots_per90: float
    shots_on_target_per90: float
    crosses_per90: float
    interceptions_per90: float
    tackles_won_per90: float
    fouls_committed_per90: float
    fouls_drawn_per90: float
    offsides_per90: float
    yellow_cards_per90: float
    red_cards_per90: float

    key_passes: int | None
    big_chances_created: int | None
    successful_dribbles: int | None
    xg_per90: float | None
    xa_per90: float | None
    key_passes_per90: float | None
    dribbles_per90: float | None
    final_third_passes_per90: float | None
    pass_completion_pct: float | None
    aerial_win_pct: float | None
    sofascore_minutes: int | None

    # Goalkeeper-only stats; null for outfield players.
    goals_against_per90: float | None
    save_pct: float | None
    clean_sheet_pct: float | None
    penalty_saves: int | None
    penalties_faced: int | None
    penalties_missed: int | None

    # Percentile (0-100) within same-position, reliable-minutes peers; higher
    # is always better, regardless of whether the underlying stat is
    # inverted (e.g. goals conceded). Null if there weren't enough peers.
    radar: list[dict]


class ModelMetrics(BaseModel):
    screening: dict
    baseline: dict
    lightgbm: dict
    model_selection: dict
    # Out-of-sample comparison with summer 2026 transfer fees.
    transfer_validation: dict


class Contribution(BaseModel):
    feature: str
    label: str
    player_value: float | None
    impact: float
    direction: str


class ContributionGroup(BaseModel):
    group: str
    impact: float


class Explanation(BaseModel):
    predicted_value_eur: float
    base_value_eur: float
    model_type: str
    contributions: list[Contribution]
    groups: list[ContributionGroup]


class SimilarPlayer(BaseModel):
    player_id: int
    name: str
    club: str
    sub_position: str
    age: float
    market_value_eur: int
    estimated_market_value_eur: float | None
    similarity: float
    shared_traits: list[str]
