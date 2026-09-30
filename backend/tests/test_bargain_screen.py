import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from app.utils.bargains import PERFORMANCE_STATS, assess_bargain, performance_scores
from app.utils.name_matching import birth_year_matches

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
from match_players import match_players
from build_training_set import match_other_leagues


def test_wrong_birth_year_exact_name_cannot_override_correct_person():
    fb = pd.DataFrame([dict(Player='Joshua King', Squad='Fulham', Born=2007)])
    tm = pd.DataFrame([
        dict(player_id=1, name='Joshua King', current_club_name='Elsewhere', date_of_birth='1992-01-15', sub_position='Forward'),
        dict(player_id=2, name='Josh King', current_club_name='Fulham FC', date_of_birth='2007-01-03', sub_position='Midfielder'),
    ])
    vals = pd.DataFrame([dict(player_id=i, date='2026-01-01', market_value_in_eur=i*1000000) for i in [1,2]])
    matched, *_ = match_players(fb, tm, vals)
    assert matched.iloc[0].player_id == 2
    assert matched.iloc[0].market_value_in_eur == 2000000
    rejected, *_ = match_players(fb, tm.iloc[:1], vals)
    assert rejected.empty
    other, _ = match_other_leagues(fb, tm.iloc[:1], vals)
    assert other.empty


@pytest.mark.parametrize('born,dob', [(None, '2000-01-01'), (2000, None), (2000, '1999-01-01')])
def test_missing_or_conflicting_birth_year_rejected(born, dob):
    assert not birth_year_matches({'Born': born}, {'date_of_birth': dob})


def good_row():
    return dict(identity_verified=True, Min=2200, market_value_in_eur=5000000,
                model_supported=True, position_group='FW', performance_percentile=70,
                conservative_gap_eur=1000000)


@pytest.mark.parametrize('field,value', [('identity_verified', False), ('Min', 1799),
    ('market_value_in_eur', 999999), ('model_supported', False), ('position_group', 'GK'),
    ('performance_percentile', 49), ('performance_percentile', np.nan), ('conservative_gap_eur', 0), ('conservative_gap_eur', np.nan)])
def test_each_screen_can_reject_a_large_raw_gap(field, value):
    row = good_row()
    row['value_gap_pct'] = 1000
    assert assess_bargain(row) == 'Passes screening'
    row[field] = value
    assert assess_bargain(row) != 'Passes screening'


def test_low_minutes_rate_is_shrunk_toward_peers():
    stats = PERFORMANCE_STATS['FW']
    df = pd.DataFrame({'position_group': ['FW'] * 4, 'Min': [900, 3000, 3000, 3000],
                       **{s: [.60, .58, .1, .1] for s in stats}})
    scores = performance_scores(df)
    assert scores.between(0, 100).all()
    assert scores[1] > scores[0]  # Playing-time shrinkage reverses the noisy raw ordering.
    # Position-relative production is independent of price or player name.
    df['market_value_in_eur'] = [1, 100000000, 50, 20]
    pd.testing.assert_series_equal(scores, performance_scores(df))


def test_saved_folds_exclude_every_scored_player_from_training():
    rankings = pd.read_csv(ROOT / 'model/artifacts/rankings.csv')
    for (position, fold), rows in rankings.groupby(['position_group', 'model_fold']):
        group = 'goalkeepers' if position == 'GK' else 'outfield'
        meta = json.loads((ROOT / f'model/artifacts/{group}_fold_{int(fold)}.json').read_text())
        train, held_out = set(meta['train_player_ids']), set(meta['held_out_player_ids'])
        assert train.isdisjoint(held_out)
        assert set(rows.player_id) <= held_out
        assert set(rows.player_id).isdisjoint(train)
        assert (rows.conservative_value_eur <= rows.estimated_market_value_eur).all()
