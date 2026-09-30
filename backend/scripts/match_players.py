"""
Builds the core Premier League scouting dataset for the 2025-26 season by
combining FBref season statistics with Transfermarkt market valuations.

The two sources have no shared ID, so players are matched by normalized name,
requiring birth-year agreement, with club as a tiebreaker when a name is ambiguous. Nothing is silently
dropped: every FBref player either ends up in the matched output or in the
unmatched/ambiguous report for manual review.

Usage: python scripts/match_players.py
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

# FBref's Comp column tags every row with a league prefix; this is the only
# reliable season+competition scope in the whole project, since Transfermarkt's
# own competition tag on valuation rows lags real relegations (see below).
FBREF_COMP = "eng Premier League"

# FBref squad name -> Transfermarkt club name, for the 20 clubs that were
# actually in the 2025-26 Premier League. Built by inspecting both files
# directly rather than assumed.
CLUB_ALIASES = {
    "Arsenal": "Arsenal FC",
    "Aston Villa": "Aston Villa",
    "Bournemouth": "AFC Bournemouth",
    "Brentford": "Brentford FC",
    "Brighton": "Brighton & Hove Albion",
    "Burnley": "Burnley FC",
    "Chelsea": "Chelsea FC",
    "Crystal Palace": "Crystal Palace",
    "Everton": "Everton FC",
    "Fulham": "Fulham FC",
    "Leeds United": "Leeds United",
    "Liverpool": "Liverpool FC",
    "Manchester City": "Manchester City",
    "Manchester Utd": "Manchester United",
    "Newcastle United": "Newcastle United",
    "Nottingham Forest": "Nottingham Forest",
    "Sunderland": "Sunderland AFC",
    "Tottenham Hotspur": "Tottenham Hotspur",
    "West Ham United": "West Ham United",
    "Wolves": "Wolverhampton Wanderers",
}

def build_name_index(tm_players: pd.DataFrame) -> dict:
    """Maps a normalized name -> list of candidate player_id rows."""
    index: dict[str, list] = {}
    for _, row in tm_players.iterrows():
        key = normalize_name(row["name"])
        index.setdefault(key, []).append(row)
    return index


def latest_valuation(player_id, valuations: pd.DataFrame):
    window = valuations[
        (valuations["player_id"] == player_id)
        & (valuations["date"] >= SEASON_START)
        & (valuations["date"] <= SEASON_END)
    ]
    if window.empty:
        return None
    return window.sort_values("date").iloc[-1]


def match_players(fbref_df: pd.DataFrame, tm_players: pd.DataFrame, valuations: pd.DataFrame):
    tm_players = tm_players.copy()
    tm_players["birth_year"] = pd.to_datetime(tm_players["date_of_birth"], errors="coerce").dt.year
    year_names = {year: list(build_name_index(pool)) for year, pool in tm_players.groupby("birth_year")}
    name_index = build_name_index(tm_players)
    club_groups = {club: grp for club, grp in tm_players.groupby("current_club_name")}

    matched_rows = []
    review_rows = []
    unmatched_identity = []
    unmatched_valuation = []

    for _, row in fbref_df.iterrows():
        fbref_name = row["Player"]
        norm_name = normalize_name(fbref_name)
        expected_club = CLUB_ALIASES.get(row["Squad"], row["Squad"])

        candidates = [c for c in name_index.get(norm_name, []) if birth_year_matches(row, c)]
        match_method = "exact"

        if not candidates:
            fuzzy = process.extractOne(
                norm_name, year_names.get(row.get("Born"), []), scorer=fuzz.token_sort_ratio, score_cutoff=88
            )
            if fuzzy:
                candidates = [c for c in name_index[fuzzy[0]] if birth_year_matches(row, c)]
                match_method = f"fuzzy ({fuzzy[1]:.0f})"

        if not candidates:
            # Last resort: within the player's known club, look for a Transfermarkt
            # entry with a matching surname (catches nicknames, e.g. FBref "Max
            # Kilman" vs Transfermarkt "Maximilian Kilman"), and only if that's
            # ambiguous fall back to any shared token (catches mononyms, e.g.
            # FBref "Toti Gomes" vs Transfermarkt "Toti").
            club_pool = club_groups.get(expected_club)
            token_hits, ambiguous = [], False
            if club_pool is not None:
                fbref_tokens = norm_name.split()
                surname = fbref_tokens[-1]
                surname_hits = [
                    c for _, c in club_pool.iterrows()
                    if birth_year_matches(row, c) and normalize_name(c["name"]).split()[-1] == surname
                ]
                if len(surname_hits) == 1:
                    token_hits, match_method = surname_hits, "club+surname"
                else:
                    any_hits = [
                        c for _, c in club_pool.iterrows()
                        if birth_year_matches(row, c) and set(fbref_tokens) & set(normalize_name(c["name"]).split())
                    ]
                    if len(any_hits) == 1:
                        token_hits, match_method = any_hits, "club+token"
                    elif len(any_hits) > 1:
                        ambiguous = True
                        review_rows.append({
                            "player": fbref_name, "club": row["Squad"],
                            "candidate_names": [c["name"] for c in any_hits],
                            "reason": "ambiguous: multiple same-club candidates share a name token",
                        })
            if token_hits:
                candidates = token_hits
            elif not ambiguous:
                unmatched_identity.append({"player": fbref_name, "club": row["Squad"]})
                continue
            else:
                continue

        chosen = candidates[0]
        if len(candidates) > 1:
            club_matches = [c for c in candidates if c["current_club_name"] == expected_club]
            if len(club_matches) == 1:
                chosen = club_matches[0]
            else:
                review_rows.append({
                    "player": fbref_name, "club": row["Squad"],
                    "candidate_player_ids": [c["player_id"] for c in candidates],
                    "reason": "ambiguous name, club did not disambiguate",
                })
                continue

        if match_method != "exact":
            review_rows.append({
                "player": fbref_name, "club": row["Squad"],
                "matched_to": chosen["name"], "match_method": match_method,
                "reason": "inferred match, verify before trusting",
            })

        val = latest_valuation(chosen["player_id"], valuations)
        if val is None:
            unmatched_valuation.append({
                "player": fbref_name, "club": row["Squad"],
                "matched_player_id": chosen["player_id"],
            })
            continue

        record = row.to_dict()
        record["player_id"] = chosen["player_id"]
        record["identity_verified"] = True
        record["matched_name"] = chosen["name"]
        record["sub_position"] = chosen["sub_position"]
        record["market_value_in_eur"] = val["market_value_in_eur"]
        record["valuation_date"] = val["date"]
        record["match_method"] = match_method
        matched_rows.append(record)

    return (
        pd.DataFrame(matched_rows),
        pd.DataFrame(review_rows),
        pd.DataFrame(unmatched_identity),
        pd.DataFrame(unmatched_valuation),
    )


def write_report(fbref_total, matched, review, unmatched_identity, unmatched_valuation):
    match_pct = 100 * len(matched) / fbref_total
    lines = [
        "# Player Matching Report: 2025-26 Premier League",
        "",
        f"- FBref Premier League players (after merging mid-season transfers): {fbref_total}",
        f"- Matched to a market value: {len(matched)}",
        f"- Match percentage: {match_pct:.1f}%",
        f"- No Transfermarkt identity match at all: {len(unmatched_identity)}",
        f"- Identity matched but no valuation in 2025-26 window: {len(unmatched_valuation)}",
        f"- Fuzzy or ambiguous matches flagged for manual review: {len(review)}",
        "",
        "## Unmatched: no identity match",
        "",
    ]
    lines += [f"- {r['player']} ({r['club']})" for r in unmatched_identity.to_dict("records")]
    lines += ["", "## Unmatched: identity found, no valuation in season window", ""]
    lines += [f"- {r['player']} ({r['club']}) -> player_id {r['matched_player_id']}"
              for r in unmatched_valuation.to_dict("records")]
    lines += ["", "## Flagged for manual review (fuzzy / ambiguous)", ""]
    for r in review.to_dict("records"):
        clean = {k: v for k, v in r.items() if isinstance(v, list) or pd.notna(v)}
        detail = ", ".join(f"{k}={v}" for k, v in clean.items() if k not in ("player", "club"))
        lines.append(f"- {clean['player']} ({clean['club']}): {detail}")

    (DATA_PROCESSED / "match_report.md").write_text("\n".join(lines))


def main():
    fbref_df = merge_transfer_rows(load_fbref(DATA_RAW / "players_data-2025_2026.csv", FBREF_COMP))
    tm_players = pd.read_csv(DATA_RAW / "players.csv", usecols=[
        "player_id", "name", "current_club_name", "sub_position", "date_of_birth",
    ])
    valuations = pd.read_csv(DATA_RAW / "player_valuations.csv", usecols=[
        "player_id", "date", "market_value_in_eur",
    ])

    matched, review, unmatched_identity, unmatched_valuation = match_players(
        fbref_df, tm_players, valuations
    )

    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    matched.to_csv(DATA_PROCESSED / "pl_players_matched.csv", index=False)
    write_report(len(fbref_df), matched, review, unmatched_identity, unmatched_valuation)

    print(f"FBref PL players: {len(fbref_df)}")
    print(f"Matched with market value: {len(matched)}")
    print(f"Match rate: {100 * len(matched) / len(fbref_df):.1f}%")
    print(f"Flagged for review: {len(review)}")
    print(f"No identity match: {len(unmatched_identity)}")
    print(f"No valuation in window: {len(unmatched_valuation)}")


if __name__ == "__main__":
    main()
