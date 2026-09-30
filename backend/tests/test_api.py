import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    res = client.get("/api/health")
    assert res.status_code == 200
    assert res.json() == {"status": "ok"}


def test_list_players_returns_full_universe():
    res = client.get("/api/players")
    assert res.status_code == 200
    players = res.json()
    assert len(players) >= 500
    assert len({p["player_id"] for p in players}) == len(players)


def test_list_players_filter_by_position():
    res = client.get("/api/players", params={"position": "GK"})
    players = res.json()
    assert len(players) > 0
    assert all(p["position_group"] == "GK" for p in players)


def test_get_player_valid_id():
    player_id = client.get("/api/players").json()[0]["player_id"]
    res = client.get(f"/api/players/{player_id}")
    assert res.status_code == 200
    assert res.json()["player_id"] == player_id


def test_get_player_unknown_id_returns_404():
    res = client.get("/api/players/999999999")
    assert res.status_code == 404


def test_get_player_non_integer_id_returns_422():
    res = client.get("/api/players/not-a-number")
    assert res.status_code == 422


def test_rankings_only_includes_eligible_players():
    res = client.get("/api/rankings")
    rankings = res.json()
    assert all(p["eligible_for_ranking"] for p in rankings)


def test_rankings_sorted_by_conservative_gap_descending_by_default():
    rankings = client.get("/api/rankings").json()
    gaps = [p["conservative_gap_eur"] for p in rankings]
    assert gaps == sorted(gaps, reverse=True)


def test_rankings_invalid_order_param_returns_422():
    res = client.get("/api/rankings", params={"order": "sideways"})
    assert res.status_code == 422


def test_clubs_returns_twenty_premier_league_clubs():
    res = client.get("/api/clubs")
    assert res.status_code == 200
    assert len(res.json()) == 20


def test_positions_returns_four_groups():
    res = client.get("/api/positions")
    assert set(res.json()) == {"GK", "DF", "MF", "FW"}


def test_model_metrics_has_required_sections():
    res = client.get("/api/model/metrics")
    assert res.status_code == 200
    body = res.json()
    assert set(body.keys()) == {"baseline", "lightgbm", "model_selection", "screening", "transfer_validation"}


@pytest.mark.parametrize("position", ["GK", "DF", "MF", "FW"])
def test_explanation_available_for_reliable_minutes_player_of_each_position(position):
    players = client.get("/api/players", params={"position": position}).json()
    reliable = next(p for p in players if p["meets_minutes_threshold"])
    res = client.get(f"/api/players/{reliable['player_id']}/explanation")
    assert res.status_code == 200
    body = res.json()
    assert body["predicted_value_eur"] > 0
    assert len(body["contributions"]) > 0


def test_explanation_404_for_below_threshold_player():
    players = client.get("/api/players").json()
    unreliable = next(p for p in players if not p["meets_minutes_threshold"])
    res = client.get(f"/api/players/{unreliable['player_id']}/explanation")
    assert res.status_code == 404


def test_explanation_404_for_unknown_player():
    res = client.get("/api/players/999999999/explanation")
    assert res.status_code == 404


def test_king_identity_and_shortlist_rules():
    players = client.get("/api/players").json()
    king = next(p for p in players if p["player_id"] == 1011131)
    assert king["name"] == "Josh King"
    assert king["club"] == "Fulham"
    assert king["market_value_eur"] == 25000000
    assert not king["eligible_for_ranking"]
    assert all(p["player_id"] != 91059 for p in players)
    for p in client.get("/api/rankings").json():
        assert p["minutes"] >= 1800
        assert p["performance_percentile"] >= 50
        assert p["conservative_gap_eur"] > 0
        assert p["position_group"] != "GK"


def test_explanations_reconstruct_the_displayed_held_out_prediction():
    from app.services.data_store import load_players
    rows = load_players().dropna(subset=["model_fold"])
    for _, group in rows.groupby(["position_group", "model_fold"]):
        p = group.iloc[0]
        explanation = client.get(f"/api/players/{int(p.player_id)}/explanation").json()
        assert explanation["predicted_value_eur"] == pytest.approx(p.estimated_market_value_eur, rel=1e-6)


def test_similar_players_share_position_and_exclude_self():
    ranked = client.get("/api/rankings").json()[0]
    res = client.get(f"/api/players/{ranked['player_id']}/similar", params={"limit": 4})
    assert res.status_code == 200
    similar = res.json()
    assert len(similar) == 4
    assert ranked["player_id"] not in {p["player_id"] for p in similar}
    scores = [p["similarity"] for p in similar]
    assert scores == sorted(scores, reverse=True)
    for p in similar:
        detail = client.get(f"/api/players/{p['player_id']}").json()
        assert detail["position_group"] == ranked["position_group"]
        assert detail["meets_minutes_threshold"]


def test_similar_players_below_minutes_threshold_returns_404():
    players = client.get("/api/players").json()
    low = next(p for p in players if not p["meets_minutes_threshold"])
    assert client.get(f"/api/players/{low['player_id']}/similar").status_code == 404


def test_explanation_groups_sum_to_the_displayed_estimate():
    """Grouped themes must add up exactly to the estimate they explain."""
    import math
    player = next(p for p in client.get("/api/players").json() if p["meets_minutes_threshold"])
    body = client.get(f"/api/players/{player['player_id']}/explanation").json()
    total = sum(g["impact"] for g in body["groups"])
    expected = math.log1p(body["predicted_value_eur"]) - math.log1p(body["base_value_eur"])
    assert abs(total - expected) < 1e-2
    assert "Other stats" not in {g["group"] for g in body["groups"]}
