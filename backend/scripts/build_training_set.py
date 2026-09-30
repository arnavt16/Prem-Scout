"""Build Big-5 training data using unique name plus birth-year matches.
Premier League rows come from match_players.py. Unresolved identities and
missing valuations are excluded rather than assigned a guessed target.
"""

import sys
from pathlib import Path

import pandas as pd
from rapidfuzz import fuzz, process

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.utils.name_matching import normalize_name, birth_year_matches  # noqa: E402
from app.utils.fbref_cleaning import load_fbref, merge_transfer_rows  # noqa: E402

DATA_RAW = Path(__file__).resolve().parent.parent / "data" / "raw"
DATA_PROCESSED = Path(__file__).resolve().parent.parent / "data" / "processed"

SEASON_START = "2025-07-01"
SEASON_END = "2026-06-30"

OTHER_LEAGUES = ["es La Liga", "it Serie A", "fr Ligue 1", "de Bundesliga"]


def build_name_index(tm_players: pd.DataFrame) -> dict:
    index: dict[str, list] = {}
    for _, row in tm_players.iterrows():
        index.setdefault(normalize_name(row["name"]), []).append(row)
    return index


def latest_valuation(player_id, valuations: pd.DataFrame):
    window = valuations[
        (valuations["player_id"] == player_id)
        & (valuations["date"] >= SEASON_START)
        & (valuations["date"] <= SEASON_END)
    ]
    return None if window.empty else window.sort_values("date").iloc[-1]


def match_other_leagues(fbref_df, tm_players, valuations):
    tm_players = tm_players.copy()
    tm_players["birth_year"] = pd.to_datetime(tm_players["date_of_birth"], errors="coerce").dt.year
    year_names = {year: list(build_name_index(pool)) for year, pool in tm_players.groupby("birth_year")}
    name_index = build_name_index(tm_players)

    matched_rows, unmatched = [], 0
    for _, row in fbref_df.iterrows():
        norm_name = normalize_name(row["Player"])
        candidates = [c for c in name_index.get(norm_name, []) if birth_year_matches(row, c)]

        if not candidates:
            fuzzy = process.extractOne(
                norm_name, year_names.get(row.get("Born"), []), scorer=fuzz.token_sort_ratio, score_cutoff=92
            )
            if fuzzy:
                candidates = [c for c in name_index[fuzzy[0]] if birth_year_matches(row, c)]

        if len(candidates) != 1:
            unmatched += 1
            continue

        chosen = candidates[0]
        val = latest_valuation(chosen["player_id"], valuations)
        if val is None:
            unmatched += 1
            continue

        record = row.to_dict()
        record["player_id"] = chosen["player_id"]
        record["identity_verified"] = True
        record["matched_name"] = chosen["name"]
        record["sub_position"] = chosen["sub_position"]
        record["market_value_in_eur"] = val["market_value_in_eur"]
        record["valuation_date"] = val["date"]
        matched_rows.append(record)

    return pd.DataFrame(matched_rows), unmatched


def main():
    tm_players = pd.read_csv(DATA_RAW / "players.csv", usecols=[
        "player_id", "name", "current_club_name", "sub_position", "date_of_birth",
    ])
    valuations = pd.read_csv(DATA_RAW / "player_valuations.csv", usecols=[
        "player_id", "date", "market_value_in_eur",
    ])

    other_df = load_fbref(DATA_RAW / "players_data-2025_2026.csv")
    other_df = other_df[other_df["Comp"].isin(OTHER_LEAGUES)]
    other_df = merge_transfer_rows(other_df, group_cols=("Player", "Comp"))

    matched_other, unmatched = match_other_leagues(other_df, tm_players, valuations)
    matched_other["is_premier_league"] = False
    print(f"Other Big-5 leagues: {len(other_df)} players, "
          f"{len(matched_other)} matched ({100 * len(matched_other) / len(other_df):.1f}%), "
          f"{unmatched} skipped (ambiguous or no valuation)")

    pl_path = DATA_PROCESSED / "pl_players_matched.csv"
    if not pl_path.exists():
        raise SystemExit("Run scripts/match_players.py first to build pl_players_matched.csv")
    matched_pl = pd.read_csv(pl_path)
    matched_pl["is_premier_league"] = True

    shared_cols = [c for c in matched_pl.columns if c in matched_other.columns]
    training_set = pd.concat(
        [matched_pl[shared_cols], matched_other[shared_cols]], ignore_index=True
    )

    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    training_set.to_csv(DATA_PROCESSED / "training_set_raw.csv", index=False)
    print(f"Combined training set: {len(training_set)} players "
          f"({matched_pl.shape[0]} Premier League + {len(matched_other)} other leagues)")


if __name__ == "__main__":
    main()
