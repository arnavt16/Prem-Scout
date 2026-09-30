export function formatEur(value) {
  if (value === null || value === undefined) return 'N/A';
  const abs = Math.abs(value);
  if (abs >= 1_000_000_000) return `€${(value / 1_000_000_000).toFixed(2)}B`;
  if (abs >= 1_000_000) return `€${(value / 1_000_000).toFixed(1)}M`;
  if (abs >= 1_000) return `€${(value / 1_000).toFixed(0)}K`;
  return `€${value.toFixed(0)}`;
}

export function formatPct(value, { showSign = true } = {}) {
  if (value === null || value === undefined) return 'N/A';
  const sign = showSign && value > 0 ? '+' : '';
  return `${sign}${value.toFixed(1)}%`;
}

export function plural(n, word) {
  return `${n} ${word}${n === 1 ? '' : 's'}`;
}

/** "2026-06-03" -> "3 June 2026". */
export function formatDate(iso) {
  const date = new Date(`${String(iso).slice(0, 10)}T00:00:00`);
  return Number.isNaN(date.getTime())
    ? String(iso)
    : date.toLocaleDateString('en-GB', { day: 'numeric', month: 'long', year: 'numeric' });
}
