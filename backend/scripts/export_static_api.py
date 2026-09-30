"""
Exports every API response the frontend uses as static JSON under
frontend/public/data, mirroring the API's URL layout. The data is a fixed
season snapshot, so the deployed site can serve these files directly instead
of waiting for a sleeping backend to boot.

Responses come from the real FastAPI app (via TestClient), so the files are
exactly what the live API would return. Rerun after generate_rankings.py.

Usage: python scripts/export_static_api.py
"""

import json
import shutil
import sys
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.main import app  # noqa: E402

OUT = Path(__file__).resolve().parents[2] / "frontend" / "public" / "data"


def main():
    client = TestClient(app)
    if OUT.exists():
        shutil.rmtree(OUT)

    def save(path):
        res = client.get(f"/api/{path}")
        if res.status_code == 404:
            return False
        res.raise_for_status()
        target = OUT / f"{path}.json"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(res.json(), separators=(",", ":")))
        return True

    for path in ["players", "rankings", "clubs", "positions", "model/metrics"]:
        save(path)

    players = client.get("/api/players").json()
    counts = {"detail": 0, "explanation": 0, "similar": 0}
    for p in players:
        pid = p["player_id"]
        counts["detail"] += save(f"players/{pid}")
        counts["explanation"] += save(f"players/{pid}/explanation")
        counts["similar"] += save(f"players/{pid}/similar")

    size_mb = sum(f.stat().st_size for f in OUT.rglob("*.json")) / 1e6
    print(f"Exported {len(players)} players {counts} to {OUT} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
