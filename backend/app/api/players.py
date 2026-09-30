from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from app.schemas.player import Explanation, PlayerDetail, PlayerSummary, SimilarPlayer
from app.services import explanation_service, player_service, similarity_service

router = APIRouter(prefix="/api", tags=["players"])


class FilterParams:
    def __init__(
        self,
        club: str | None = None,
        position: str | None = None,
        min_age: float | None = None,
        max_age: float | None = None,
        min_minutes: int | None = None,
        min_value: int | None = None,
        max_value: int | None = None,
        sort_by: str | None = None,
        order: Annotated[str, Query(pattern="^(asc|desc)$")] = "desc",
    ):
        self.as_dict = dict(
            club=club, position=position, min_age=min_age, max_age=max_age,
            min_minutes=min_minutes, min_value=min_value, max_value=max_value,
            sort_by=sort_by, order=order,
        )


@router.get("/players", response_model=list[PlayerSummary])
def get_players(params: Annotated[FilterParams, Depends()]):
    return player_service.list_players(**params.as_dict)


@router.get("/players/{player_id}", response_model=PlayerDetail)
def get_player(player_id: int):
    player = player_service.get_player(player_id)
    if player is None:
        raise HTTPException(status_code=404, detail=f"No player with id {player_id}")
    return player


@router.get("/players/{player_id}/explanation", response_model=Explanation)
def get_player_explanation(player_id: int):
    explanation = explanation_service.explain_player(player_id)
    if explanation is None:
        raise HTTPException(
            status_code=404,
            detail=f"No explanation available for player {player_id} "
                    "(unknown player, or below the minutes threshold)",
        )
    return explanation


@router.get("/players/{player_id}/similar", response_model=list[SimilarPlayer])
def get_similar_players(player_id: int, limit: Annotated[int, Query(ge=1, le=20)] = 5):
    similar = similarity_service.similar_players(player_id, limit)
    if similar is None:
        raise HTTPException(
            status_code=404,
            detail=f"No similar players available for player {player_id} "
                    "(unknown player, or below the minutes threshold)",
        )
    return similar


@router.get("/rankings", response_model=list[PlayerSummary])
def get_rankings(params: Annotated[FilterParams, Depends()]):
    kwargs = params.as_dict
    if kwargs["sort_by"] is None:
        kwargs["sort_by"] = "conservative_gap_eur"
    return player_service.list_rankings(**kwargs)


@router.get("/clubs", response_model=list[str])
def get_clubs():
    return player_service.list_clubs()


@router.get("/positions", response_model=list[str])
def get_positions():
    return player_service.list_positions()
