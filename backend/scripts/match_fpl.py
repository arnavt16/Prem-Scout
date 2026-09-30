"""
Links Fantasy Premier League 2025-26 season data (full 38 matchdays, from the
vaastav/Fantasy-Premier-League community archive) to the matched players.

Unlike SofaScore, FPL records dates of birth, so identity rests on birth year
plus name (and club when the name is ambiguous), the same standard the
FBref <-> Transfermarkt matching uses.

Usage: python scripts/match_fpl.py (run clean_data.py first)
Input:  data/raw/fpl_2025_26_players_raw.csv, data/raw/fpl_2025_26_teams.csv
Output: data/processed/fpl_matched.csv, data/processed/fpl_match_report.md
"""

from pathlib import Path
import sys

import pandas as pd
from rapidfuzz import fuzz

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.utils.name_matching import normalize_name  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
PROCESSED = ROOT / "data" / "processed"

# FPL short team name -> FBref Squad.
TEAM_NAMES = {
    "Leeds": "Leeds United", "Man City": "Manchester City", "Man Utd": "Manchester Utd",
    "Newcastle": "Newcastle United", "Nott'm Forest": "Nottingham Forest",
    "Spurs": "Tottenham Hotspur", "West Ham": "West Ham United",
}
NAME_THRESHOLD = 80
# Season performance columns carried into features. Price, ownership,
# transfers and form are deliberately excluded: they track popularity and
# reputation, which would let market sentiment leak into a model meant to
# judge the market.
KEEP = ["minutes", "starts", "influence", "creativity", "threat", "bps", "defensive_contribution",
        "recoveries", "tackles", "clearances_blocks_interceptions", "expected_goals_conceded",
        "goals_conceded", "clean_sheets", "expected_goals", "expected_assists"]


def _fpl_names(row) -> set[str]:
    names = {normalize_name(f"{row.first_name} {row.second_name}"), normalize_name(str(row.web_name))}
    if isinstance(row.known_name, str) and row.known_name:
        names.add(normalize_name(row.known_name))
    return names


def match(fpl: pd.DataFrame, players: pd.DataFrame):
    fpl = fpl.assign(_names=fpl.apply(_fpl_names, axis=1),
                     _birth_year=pd.to_datetime(fpl.birth_date, errors="coerce").dt.year)
    rows, report = [], []
    for _, p in players.iterrows():
        names = {normalize_name(p.Player), normalize_name(str(p.matched_name))}
        same_year = fpl[fpl._birth_year == p.Born]
        scores = same_year._names.map(lambda ns: max(fuzz.token_set_ratio(a, b) for a in names for b in ns))
        candidates = same_year[scores >= NAME_THRESHOLD]
        same_club = candidates[candidates.club == p.Squad]
        if len(same_club) == 1:
            pick, how = same_club.iloc[0], "birth year + name, same club"
        elif len(candidates) == 1:
            pick, how = candidates.iloc[0], "birth year + name, different club"
        else:
            report.append((p.Player, p.Squad, "", f"{len(candidates)} candidates"))
            continue
        report.append((p.Player, p.Squad, f"{pick.first_name} {pick.second_name}", how))
        rows.append({"player_id": int(p.player_id), **{f"fpl_{c}": pick[c] for c in KEEP}})
    matched = pd.DataFrame(rows)
    return matched, pd.DataFrame(report, columns=["fbref_name", "club", "fpl_name", "status"])


def main():
    fpl = pd.read_csv(RAW / "fpl_2025_26_players_raw.csv")
    teams = pd.read_csv(RAW / "fpl_2025_26_teams.csv").set_index("id")["name"]
    fpl["club"] = fpl.team.map(teams).replace(TEAM_NAMES)
    clean = pd.read_csv(PROCESSED / "players_clean.csv")
    pl = clean[clean.is_premier_league]

    matched, report = match(fpl, pl)
    dupes = matched.duplicated(subset=[c for c in matched.columns if c != "player_id"], keep=False)
    assert not dupes.any(), "Two players claimed the same FPL row"
    matched.to_csv(PROCESSED / "fpl_matched.csv", index=False)

    reliable = pl[pl.meets_minutes_threshold]
    coverage = reliable.player_id.isin(matched.player_id).mean()
    lines = ["# FPL match report", "",
             f"PL players: {len(pl)}; matched to FPL: {len(matched)}.",
             f"Coverage of PL players with 900+ FBref minutes: {coverage:.1%}.", "",
             "| Status | Players |", "|---|---:|",
             *[f"| {k} | {v} |" for k, v in report.status.value_counts().items()], "",
             "## Not same-club matches", "", "| FBref | Club | FPL | Status |", "|---|---|---|---|",
             *[f"| {r.fbref_name} | {r.club} | {r.fpl_name} | {r.status} |"
               for r in report[report.status != "birth year + name, same club"].itertuples()]]
    (PROCESSED / "fpl_match_report.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
