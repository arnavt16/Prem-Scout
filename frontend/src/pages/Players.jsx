import { useMemo, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Alert, Box, Button, Collapse, Grid, Group, SimpleGrid, Text, Title } from '@mantine/core';
import { ClubBadge } from '../components/ClubBadge';
import { FilterSidebar } from '../components/FilterSidebar';
import { DEFAULT_FILTERS } from '../utils/filters';
import { LoadingState } from '../components/LoadingState';
import { PlayerCard } from '../components/PlayerCard';
import { useFetch } from '../hooks/useFetch';
import { api } from '../services/api';
import { clubInfo } from '../utils/clubs';
import { verdictKey } from '../utils/player';

const PAGE_SIZE = 36;

function matches(p, f) {
  const query = f.search.trim().toLowerCase();
  if (query && !p.name.toLowerCase().includes(query)) return false;
  if (f.club && p.club !== f.club) return false;
  if (f.position !== 'all' && p.position_group !== f.position) return false;
  if (p.age < f.age[0] || p.age > f.age[1]) return false;
  const valueM = p.market_value_eur / 1e6;
  if (valueM < f.value[0] || (f.value[1] < 200 && valueM > f.value[1])) return false;
  if (f.regularsOnly && p.minutes < 1800) return false;
  if (f.verdicts.length && !f.verdicts.includes(verdictKey(p))) return false;
  return true;
}

// Missing values always sort last, whatever the direction.
function sortPlayers(players, sort) {
  const key = {
    value_for_money: (p) => p.conservative_gap_eur,
    age_asc: (p) => p.age,
    name: (p) => p.name,
  }[sort] ?? ((p) => p[sort]);
  const ascending = sort === 'age_asc' || sort === 'name';
  return [...players].sort((a, b) => {
    const av = key(a);
    const bv = key(b);
    if (av == null) return bv == null ? 0 : 1;
    if (bv == null) return -1;
    if (typeof av === 'string') return av.localeCompare(bv);
    return ascending ? av - bv : bv - av;
  });
}

export function Players() {
  const [params, setParams] = useSearchParams();
  // The club lives in the URL (?club=Arsenal) so club cards, the nav link
  // and the back button all agree; other filters are local state, seeded
  // once from links like ?verdict=pick.
  const clubParam = params.get('club');
  const [localFilters, setLocalFilters] = useState(() => ({
    ...DEFAULT_FILTERS,
    position: params.get('position') ?? 'all',
    verdicts: params.get('verdict') ? [params.get('verdict')] : [],
    sort: params.get('sort') ?? DEFAULT_FILTERS.sort,
  }));
  const filters = useMemo(() => ({ ...localFilters, club: clubParam }), [localFilters, clubParam]);
  const [shown, setShown] = useState(PAGE_SIZE);
  const [filtersOpen, setFiltersOpen] = useState(false);
  const { data: players, error, loading } = useFetch(() => api.getPlayers(), []);

  const rows = useMemo(
    () => (players ? sortPlayers(players.filter((p) => matches(p, filters)), filters.sort) : []),
    [players, filters],
  );

  const updateFilters = ({ club, ...rest }) => {
    setLocalFilters({ ...rest, club: null });
    if ((club ?? null) !== clubParam) setParams(club ? { club } : {});
    setShown(PAGE_SIZE);
  };

  if (loading) return <LoadingState />;
  if (error) return <Alert color="red" title="Couldn't load players">{error}. Please refresh to retry.</Alert>;

  const club = filters.club ? clubInfo(filters.club) : null;
  return (
    <div>
      <Group gap="md" mb={4}>
        {club && <ClubBadge club={club.name} size={44} />}
        <Title order={1}>{club ? club.display : 'Player database'}</Title>
      </Group>
      <Text c="dimmed" mb="xl" maw={760}>
        {club
          ? `Every ${club.display} player from the 2025/26 season. Click a player to see their full profile.`
          : 'All 518 Premier League players from the 2025/26 season with a market value. Use the filters to narrow it down, and click any player for their radar chart, stats and our price verdict.'}
      </Text>
      <Grid gutter="xl">
        <Grid.Col span={{ base: 12, md: 3 }}>
          {/* Phones: filters fold away behind a button. Desktop: always-open sidebar. */}
          <Box hiddenFrom="md">
            <Button fullWidth variant="default" onClick={() => setFiltersOpen((o) => !o)} mb="sm">
              {filtersOpen ? 'Hide filters' : 'Filters & sorting'}
            </Button>
            <Collapse expanded={filtersOpen}>
              <FilterSidebar filters={filters} onChange={updateFilters} />
            </Collapse>
          </Box>
          <Box visibleFrom="md">
            <FilterSidebar filters={filters} onChange={updateFilters} sticky />
          </Box>
        </Grid.Col>
        <Grid.Col span={{ base: 12, md: 9 }}>
          <Text size="sm" c="dimmed" mb="sm">
            {rows.length} player{rows.length === 1 ? '' : 's'}
          </Text>
          {rows.length === 0 && <Text my="xl">No players match these filters.</Text>}
          <SimpleGrid cols={{ base: 1, xs: 2, lg: 3 }} spacing="md">
            {rows.slice(0, shown).map((p) => <PlayerCard key={p.player_id} player={p} />)}
          </SimpleGrid>
          {shown < rows.length && (
            <Group justify="center" mt="xl">
              <Button variant="light" onClick={() => setShown((n) => n + PAGE_SIZE)}>
                Show more ({rows.length - shown} left)
              </Button>
            </Group>
          )}
        </Grid.Col>
      </Grid>
    </div>
  );
}
