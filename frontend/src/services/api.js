// The site reads a pre-exported snapshot of every API response from
// /data (see backend/scripts/export_static_api.py), so pages load without
// waiting on a backend. Filtering and sorting already happen client-side.
const BASE_URL = `${import.meta.env.BASE_URL}data`;

async function get(path) {
  let res;
  try {
    res = await fetch(`${BASE_URL}${path}.json`);
  } catch {
    throw new Error('Could not load scouting data. Please check your connection and retry.');
  }
  // A missing file can come back as the SPA's index.html from dev servers.
  const isJson = res.headers.get('content-type')?.includes('json');
  if (res.status === 404 || (res.ok && !isJson)) throw new Error('Not found');
  if (!res.ok) throw new Error(`Request failed: ${res.status}`);
  return res.json();
}

export const api = {
  getPlayers: () => get('/players'),
  getPlayer: (id) => get(`/players/${id}`),
  getPlayerExplanation: (id) => get(`/players/${id}/explanation`),
  getSimilarPlayers: (id) => get(`/players/${id}/similar`),
  getRankings: () => get('/rankings'),
  getClubs: () => get('/clubs'),
  getPositions: () => get('/positions'),
  getModelMetrics: () => get('/model/metrics'),
};
