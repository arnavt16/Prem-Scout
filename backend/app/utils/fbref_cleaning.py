import pandas as pd

# Columns that are simple sums when a player has two rows from an in-season
# transfer between two clubs in the same competition. Rate/percentage columns
# are deliberately excluded here and recomputed later from these raw totals,
# since averaging a percentage across unequal minutes is not meaningful.
SUMMABLE_COLUMNS = [
    "MP", "Starts", "Min", "Gls", "Ast", "G+A", "G-PK", "PK", "PKatt",
    "CrdY", "CrdR", "Sh", "SoT", "Fls", "Fld", "Off", "Crs", "Int", "TklW", "OG",
]


def merge_transfer_rows(df: pd.DataFrame, group_cols=("Player",)) -> pd.DataFrame:
    """Collapse a player's multiple rows (mid-season transfer within the same
    competition) into one, summing raw counting stats and keeping the club
    where they played the most minutes as their season club."""
    merged_rows = []
    for _, group in df.groupby(list(group_cols)):
        if len(group) == 1:
            merged_rows.append(group.iloc[0].to_dict())
            continue

        primary = group.loc[group["Min"].idxmax()].to_dict()
        clubs = group.sort_values("Min", ascending=False)["Squad"].tolist()
        for col in SUMMABLE_COLUMNS:
            if col in group.columns:
                primary[col] = pd.to_numeric(group[col], errors="coerce").sum()
        primary["Squad"] = clubs[0]
        primary["clubs_this_season"] = ", ".join(clubs)
        merged_rows.append(primary)

    result = pd.DataFrame(merged_rows)
    if "clubs_this_season" not in result.columns:
        result["clubs_this_season"] = result["Squad"]
    result["clubs_this_season"] = result["clubs_this_season"].fillna(result["Squad"])
    return result


def load_fbref(raw_path, comp_filter: str | None = None) -> pd.DataFrame:
    df = pd.read_csv(raw_path)
    if comp_filter:
        df = df[df["Comp"] == comp_filter].copy()
    df["Min"] = df["Min"].astype(str).str.replace(",", "").astype(int)
    return df
