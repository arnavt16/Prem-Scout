"""The deployed site reads frontend/public/data instead of the live API, so
those files must match what the API returns for the current artifacts.
If this fails, rerun scripts/export_static_api.py."""
import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)
DATA = Path(__file__).resolve().parents[2] / "frontend" / "public" / "data"


@pytest.mark.parametrize("path", ["players", "rankings", "clubs", "positions", "model/metrics"])
def test_static_collections_match_api(path):
    assert json.loads((DATA / f"{path}.json").read_text()) == client.get(f"/api/{path}").json()


def test_static_player_files_match_api():
    for player in client.get("/api/players").json():
        pid = player["player_id"]
        for path in [f"players/{pid}", f"players/{pid}/explanation", f"players/{pid}/similar"]:
            res = client.get(f"/api/{path}")
            file = DATA / f"{path}.json"
            if res.status_code == 404:
                assert not file.exists(), path
            else:
                assert json.loads(file.read_text()) == res.json(), path
