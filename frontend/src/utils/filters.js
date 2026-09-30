export const SORT_OPTIONS = [
  { value: 'market_value_eur', label: 'Market value (highest)' },
  { value: 'estimated_market_value_eur', label: 'Our estimate (highest)' },
  { value: 'value_for_money', label: 'Best value for money' },
  { value: 'rating', label: 'Match rating (highest)' },
  { value: 'goals', label: 'Most goals' },
  { value: 'assists', label: 'Most assists' },
  { value: 'xg', label: 'Most xG (expected goals)' },
  { value: 'minutes', label: 'Most minutes' },
  { value: 'age_asc', label: 'Youngest first' },
  { value: 'name', label: 'Name (A–Z)' },
];

export const DEFAULT_FILTERS = {
  search: '', club: null, position: 'all', age: [15, 40], value: [0, 200],
  regularsOnly: false, verdicts: [], sort: 'market_value_eur',
};
