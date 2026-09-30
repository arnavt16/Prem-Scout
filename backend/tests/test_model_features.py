import pandas as pd

from app.utils.model_features import build_matrix


def test_single_row_batch_still_gets_correct_position_dummy():
    """Regression test: build_matrix used to only create position dummy
    columns when a batch contained more than one distinct position, which
    is never true for a single-player request. A defender's pos_DF flag
    would silently be 0 instead of 1."""
    df = pd.DataFrame([{"position_group": "DF", "Age": 25}])
    X = build_matrix(df, ["Age", "pos_DF", "pos_MF", "pos_FW"])

    assert X.iloc[0]["pos_DF"] == 1
    assert X.iloc[0]["pos_MF"] == 0
    assert X.iloc[0]["pos_FW"] == 0


def test_multi_row_batch_gets_correct_dummies_per_row():
    df = pd.DataFrame([
        {"position_group": "DF", "Age": 25},
        {"position_group": "FW", "Age": 30},
    ])
    X = build_matrix(df, ["Age", "pos_DF", "pos_FW"])

    assert X.iloc[0]["pos_DF"] == 1 and X.iloc[0]["pos_FW"] == 0
    assert X.iloc[1]["pos_DF"] == 0 and X.iloc[1]["pos_FW"] == 1


def test_missing_feature_column_filled_with_zero():
    df = pd.DataFrame([{"position_group": "GK", "Age": 28}])
    X = build_matrix(df, ["Age", "pos_DF"])

    assert X.iloc[0]["pos_DF"] == 0
