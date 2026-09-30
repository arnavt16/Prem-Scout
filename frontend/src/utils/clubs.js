// The 20 clubs of the 2025-26 season, keyed by the club name used in the
// data. `code` is the Premier League's club code, used for crest images.
export const CLUBS = [
  { name: 'Arsenal', display: 'Arsenal', code: 3 },
  { name: 'Aston Villa', display: 'Aston Villa', code: 7 },
  { name: 'Bournemouth', display: 'Bournemouth', code: 91 },
  { name: 'Brentford', display: 'Brentford', code: 94 },
  { name: 'Brighton', display: 'Brighton', code: 36 },
  { name: 'Burnley', display: 'Burnley', code: 90 },
  { name: 'Chelsea', display: 'Chelsea', code: 8 },
  { name: 'Crystal Palace', display: 'Crystal Palace', code: 31 },
  { name: 'Everton', display: 'Everton', code: 11 },
  { name: 'Fulham', display: 'Fulham', code: 54 },
  { name: 'Leeds United', display: 'Leeds United', code: 2 },
  { name: 'Liverpool', display: 'Liverpool', code: 14 },
  { name: 'Manchester City', display: 'Manchester City', code: 43 },
  { name: 'Manchester Utd', display: 'Manchester United', code: 1 },
  { name: 'Newcastle United', display: 'Newcastle United', code: 4 },
  { name: 'Nottingham Forest', display: "Nottingham Forest", code: 17 },
  { name: 'Sunderland', display: 'Sunderland', code: 56 },
  { name: 'Tottenham Hotspur', display: 'Tottenham Hotspur', code: 6 },
  { name: 'West Ham United', display: 'West Ham United', code: 21 },
  { name: 'Wolves', display: 'Wolves', code: 39 },
];

const BY_NAME = Object.fromEntries(CLUBS.map((c) => [c.name, c]));

export function clubInfo(name) {
  return BY_NAME[name] ?? { name, display: name, code: null };
}

export function crestUrl(name) {
  const { code } = clubInfo(name);
  return code == null ? null : `https://resources.premierleague.com/premierleague/badges/t${code}.svg`;
}
