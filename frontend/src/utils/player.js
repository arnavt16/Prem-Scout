import { formatEur } from './format';

export const POSITIONS = {
  GK: { label: 'Goalkeeper', plural: 'Goalkeepers' },
  DF: { label: 'Defender', plural: 'Defenders' },
  MF: { label: 'Midfielder', plural: 'Midfielders' },
  FW: { label: 'Forward', plural: 'Forwards' },
};

/** Transfermarkt roles are hyphenated ("Centre-Back"); the site shows them as words. */
export function roleLabel(role) {
  return role ? role.replace(/-/g, ' ') : '';
}

export function positionLabel(code) {
  return POSITIONS[code]?.label ?? code;
}

// Plain-language price verdicts. "Value pick" is the model's shortlist,
// which also requires 1,800+ minutes, strong output for the position and a
// gap that survives the model's usual margin of error. The other bands
// compare the model's estimate with the market value directly.
export const VERDICTS = {
  pick: { label: 'Value pick', color: 'turf' },
  under: { label: 'Stats say worth more', color: 'teal' },
  fair: { label: 'Fair price', color: 'gray' },
  over: { label: 'Priced above stats', color: 'orange' },
  unrated: { label: 'Not enough minutes', color: 'dark' },
};

export function verdictKey(p) {
  if (!p.meets_minutes_threshold || p.estimated_market_value_eur == null) return 'unrated';
  if (p.eligible_for_ranking) return 'pick';
  const ratio = p.estimated_market_value_eur / p.market_value_eur;
  if (ratio >= 1.2) return 'under';
  if (ratio <= 0.8) return 'over';
  return 'fair';
}

export function verdict(p) {
  return { key: verdictKey(p), ...VERDICTS[verdictKey(p)] };
}

/** One or two sentences a casual fan can read. */
export function verdictSentence(p) {
  const key = verdictKey(p);
  if (key === 'unrated') {
    return `${p.name} played ${p.minutes.toLocaleString()} minutes, under the 900 we need to judge a price fairly, so there's no estimate.`;
  }
  const diff = p.estimated_market_value_eur - p.market_value_eur;
  const compare = Math.abs(diff) < 0.5e6
    ? 'almost exactly their market value'
    : `${formatEur(Math.abs(diff))} ${diff > 0 ? 'more' : 'less'} than their ${formatEur(p.market_value_eur)} market value`;
  const base = `Based on their stats, age, minutes and team, our model puts ${p.name} at about ${formatEur(p.estimated_market_value_eur)}, ${compare}.`;
  const tail = {
    pick: " They're a regular who performs well for their position, and the gap holds up even after allowing for the model's usual margin of error, which makes them one of our value picks.",
    under: ' Their stats point to a higher price, though the gap is within what the model usually gets wrong, or they miss one of the value pick checks.',
    fair: ' That lines up with the market, so the price looks about right.',
    over: " The market rates them above what their stats alone suggest. That's often reputation, potential, or things stats don't capture.",
  }[key];
  const keeper = p.position_group === 'GK' ? ' Goalkeeper estimates are rougher, so keepers are never value picks.' : '';
  return base + tail + keeper;
}
