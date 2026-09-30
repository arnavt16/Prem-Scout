import re

from unidecode import unidecode


def normalize_name(name: str) -> str:
    ascii_name = unidecode(name)
    ascii_name = re.sub(r"[-'.]", " ", ascii_name)
    ascii_name = re.sub(r"\s+", " ", ascii_name).strip().lower()
    return ascii_name


def birth_year_matches(fbref_row, candidate):
    """A name alone is not an identity: require agreement on birth year."""
    import pandas as pd
    born = pd.to_numeric(fbref_row.get("Born"), errors="coerce")
    year = candidate.get("birth_year")
    if year is None:
        dob = pd.to_datetime(candidate.get("date_of_birth"), errors="coerce")
        year = dob.year if pd.notna(dob) else None
    return pd.notna(born) and pd.notna(year) and int(born) == year
