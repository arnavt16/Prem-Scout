"""
Links SofaScore Premier League season stats (through matchday 35 of 38) to
the matched FBref/Transfermarkt players, so the richer event stats (xG, xA,
key passes, dribbles, duels, progression proxies) can join the model.

SofaScore has no birth dates, so identity rests on club + name, confirmed by
playing time: a player's SofaScore minutes (35 matchdays) must not exceed his
full-season FBref minutes and must cover a plausible share of them. Matches
failing that check are rejected rather than trusted.

Usage: python scripts/match_sofascore.py (run clean_data.py first)
Input:  data/raw/sofascore_pl_2025_26_md35.csv
Output: data/processed/sofascore_matched.csv, data/processed/sofascore_match_report.md
"""

from pathlib import Path
import sys

import pandas as pd
from rapidfuzz import fuzz

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from app.utils.name_matching import normalize_name  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw" / "sofascore_pl_2025_26_md35.csv"
PROCESSED = ROOT / "data" / "processed"

# SofaScore team name -> FBref Squad.
TEAM_NAMES = {
    "Brighton &amp; Hove Albion": "Brighton", "Liverpool FC": "Liverpool",
    "Manchester United": "Manchester Utd", "Wolverhampton": "Wolves",
}
FUZZY_THRESHOLD = 85
# SofaScore covers 35 of 38 matchdays, so its minutes should not exceed
# FBref's beyond stoppage-time counting differences (5%, or an hour for
# fringe players, where a few added-time minutes dominate the ratio).
MAX_MINUTES_RATIO = 1.05
MAX_MINUTES_SLACK = 60
# Non-exact name matches must also cover a plausible share of FBref minutes.
MIN_MINUTES_RATIO = 0.6


def _candidates(fb: pd.DataFrame, name: str, team: str):
    norm = normalize_name(name)
    same_team = fb[fb.Squad == team]
    exact = same_team[same_team._norm == norm]
    if len(exact) == 1:
        return exact.iloc[0], "exact name, same club"
    scores = same_team._norm.map(lambda n: fuzz.token_set_ratio(norm, n))
    best = scores[scores >= FUZZY_THRESHOLD]
    if len(best) == 1 or (len(best) > 1 and best.nlargest(2).diff().iloc[-1] < 0):
        return same_team.loc[best.idxmax()], f"fuzzy name ({best.max():.0f}), same club"
    # Mid-season moves: FBref keeps the club with the most minutes, SofaScore
    # the latest one. Accept only a unique exact name across the league.
    anywhere = fb[fb._norm == norm]
    if len(anywhere) == 1:
        return anywhere.iloc[0], "exact name, different club"
    return None, "no confident candidate"


def minutes_consistent(sofa_min, fbref_min, exact_same_club):
    if fbref_min <= 0:
        return False
    if sofa_min > max(fbref_min * MAX_MINUTES_RATIO, fbref_min + MAX_MINUTES_SLACK):
        return False
    return exact_same_club or sofa_min / fbref_min >= MIN_MINUTES_RATIO


def match(sofa: pd.DataFrame, fb: pd.DataFrame):
    fb = fb.assign(_norm=fb.matched_name.fillna(fb.Player).map(normalize_name))
    # FBref's own spelling is a second chance for nicknames.
    fb_alt = fb.assign(_norm=fb.Player.map(normalize_name))
    rows, report = [], []
    for _, s in sofa.iterrows():
        team = TEAM_NAMES.get(s.team_name, s.team_name)
        cand, how = _candidates(fb, s.player_name, team)
        if cand is None:
            cand, how = _candidates(fb_alt, s.player_name, team)
        if cand is None:
            report.append((s.player_name, team, "", how, s.minutesPlayed, None))
            continue
        ok = minutes_consistent(s.minutesPlayed, cand.Min, how == "exact name, same club")
        status = how if ok else f"rejected: minutes {int(s.minutesPlayed)} vs FBref {int(cand.Min)}"
        report.append((s.player_name, team, cand.Player, status, s.minutesPlayed, cand.Min))
        if ok:
            rows.append({"player_id": int(cand.player_id), **{f"ss_{c}": s[c] for c in sofa.columns
                                                              if c not in ("player_name", "team_name", "id")}})
    matched = pd.DataFrame(rows)
    dupes = matched.player_id.duplicated(keep=False)
    if dupes.any():
        # Two SofaScore rows claiming one identity means at least one is wrong.
        matched = matched[~dupes]
    return matched, pd.DataFrame(report, columns=["sofascore_name", "club", "fbref_name", "status",
                                                  "sofascore_min", "fbref_min"]), int(dupes.sum())


def main():
    sofa = pd.read_csv(RAW)
    features = pd.read_csv(PROCESSED / "players_clean.csv")
    pl = features[features.is_premier_league]
    matched, report, n_dupes = match(sofa, pl)
    matched.to_csv(PROCESSED / "sofascore_matched.csv", index=False)

    counts = report.status.str.replace(r"\(\d+\)", "", regex=True).str.replace(
        r"rejected: .*", "rejected: minutes inconsistent", regex=True).value_counts()
    reliable = pl[pl.meets_minutes_threshold]
    coverage = reliable.player_id.isin(matched.player_id).mean()
    lines = ["# SofaScore match report", "",
             f"SofaScore rows: {len(sofa)}; matched identities: {len(matched)}; "
             f"dropped as duplicate claims: {n_dupes}.",
             f"Coverage of PL players with 900+ FBref minutes: {coverage:.1%}.", "",
             "| Status | Rows |", "|---|---:|", *[f"| {k} | {v} |" for k, v in counts.items()], "",
             "## Non-exact matches and rejections", "",
             "| SofaScore | Club | FBref | Status | SofaScore min | FBref min |", "|---|---|---|---|---:|---:|"]
    review = report[report.status != "exact name, same club"]
    lines += [f"| {r.sofascore_name} | {r.club} | {r.fbref_name} | {r.status} | "
              f"{r.sofascore_min:.0f} | {'' if pd.isna(r.fbref_min) else f'{r.fbref_min:.0f}'} |"
              for r in review.itertuples()]
    (PROCESSED / "sofascore_match_report.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines[:12]))
    unmatched_reliable = reliable[~reliable.player_id.isin(matched.player_id)]
    print(f"\nReliable-minutes PL players without SofaScore stats: {len(unmatched_reliable)}")
    print(unmatched_reliable[["Player", "Squad", "Min"]].to_string(index=False))


if __name__ == "__main__":
    main()
