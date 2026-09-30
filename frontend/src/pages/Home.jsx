import { Link } from 'react-router-dom';
import {
  Alert, Anchor, Button, Card, Grid, Group, List, SimpleGrid, Stack, Table, Text, ThemeIcon, Title,
} from '@mantine/core';
import { ClubBadge } from '../components/ClubBadge';
import { LoadingState } from '../components/LoadingState';
import { PlayerCard } from '../components/PlayerCard';
import { PriceDistributionChart } from '../components/charts/PriceDistributionChart';
import { SquadValueChart } from '../components/charts/SquadValueChart';
import { StatsVsPriceChart } from '../components/charts/StatsVsPriceChart';
import { useFetch } from '../hooks/useFetch';
import { api } from '../services/api';
import { CLUBS } from '../utils/clubs';
import { formatEur } from '../utils/format';

function Section({ id, title, intro, children }) {
  return (
    <section id={id} style={{ scrollMarginTop: 80 }}>
      <Title order={2} mb={4}>{title}</Title>
      {intro && <Text c="dimmed" mb="lg" maw={820}>{intro}</Text>}
      {children}
    </section>
  );
}

function Fact({ value, label }) {
  return (
    <Card padding="md">
      <Text fw={800} size="32px" c="turf.4" lh={1.1}>{value}</Text>
      <Text size="sm" c="dimmed" mt={4}>{label}</Text>
    </Card>
  );
}

const STEPS = [
  ['Collect the season', 'Stats for every Premier League player from 2025–26: goals, expected goals, passing, dribbling, defending and match ratings, plus each player\'s Transfermarkt market value.'],
  ['Learn what drives prices', 'A model studies how stats, age, minutes played and team strength line up with market values across the league.'],
  ['Estimate every player', 'Each player gets an estimate from a version of the model that never saw their own price, so it can\'t just copy the answer.'],
  ['Flag the value picks', 'Regular starters who perform well for their position, and whose stats point to a clearly higher price even after allowing for the model\'s usual error.'],
];

export function Home() {
  const { data: players, error, loading } = useFetch(() => api.getPlayers(), []);
  const { data: metrics } = useFetch(() => api.getModelMetrics(), []);

  if (loading) return <LoadingState />;
  if (error) return <Alert color="red" title="Couldn't load the data">{error}. Please refresh to retry.</Alert>;

  const picks = players.filter((p) => p.eligible_for_ranking)
    .sort((a, b) => b.conservative_gap_eur - a.conservative_gap_eur);
  const clubs = CLUBS.map((c) => {
    const squad = players.filter((p) => p.club === c.name);
    return { ...c, players: squad.length, value: squad.reduce((sum, p) => sum + p.market_value_eur, 0),
      picks: squad.filter((p) => p.eligible_for_ranking).length };
  });
  const typicalError = metrics?.screening?.outfield?.mae_eur;
  const check = metrics?.transfer_validation;
  const sources = metrics?.screening?.methodology?.data_sources ?? [];

  return (
    <Stack gap={56}>
      <section>
        <Text c="turf.4" fw={700} tt="uppercase" size="sm" style={{ letterSpacing: 1 }}>2025–26 Premier League</Text>
        <Title order={1} size="clamp(40px, 7vw, 72px)" lh={1.05} mt={6} style={{ letterSpacing: -1.5 }}>
          Prem Scout
        </Title>
        <Text size="xl" c="dark.1" mt="md" maw={720}>
          What is every Premier League player worth? Compare each player&apos;s market value with what their
          season stats say they should cost, and find the players who look like good value.
        </Text>
        <Group mt="xl">
          <Button component={Link} to="/players" size="md">Browse all players</Button>
          <Button component="a" href="#clubs" size="md" variant="default">Pick a club</Button>
          <Button component={Link} to="/players?verdict=pick&sort=value_for_money" size="md" variant="subtle">
            See the value picks
          </Button>
        </Group>
      </section>

      <SimpleGrid cols={{ base: 2, md: 4 }}>
        <Fact value={players.length} label="players with a market value" />
        <Fact value="20" label="clubs" />
        <Fact value={picks.length} label="value picks" />
        <Fact value={typicalError ? `±${formatEur(typicalError)}` : '—'} label="typical gap between our estimate and market value" />
      </SimpleGrid>

      <Section id="clubs" title="Pick a club" intro="Jump straight to a squad. Each card shows the squad's total market value.">
        <SimpleGrid cols={{ base: 2, sm: 3, md: 4, lg: 5 }} spacing="md">
          {clubs.map((c) => (
            <Card key={c.name} component={Link} to={`/players?club=${encodeURIComponent(c.name)}`}
              className="hover-card" padding="md">
              <Stack align="center" gap={6}>
                <ClubBadge club={c.name} size={56} />
                <Text fw={700} ta="center" lh={1.2}>{c.display}</Text>
                <Text size="xs" c="dimmed">{c.players} players · {formatEur(c.value)}</Text>
                {c.picks > 0 && <Text size="xs" c="turf.4" fw={600}>{c.picks} value pick{c.picks > 1 ? 's' : ''}</Text>}
              </Stack>
            </Card>
          ))}
        </SimpleGrid>
      </Section>

      <Section title="Value picks" intro="Regular starters whose stats point to a clearly higher price than the market pays. A starting point for scouting, not a guarantee (see below).">
        <SimpleGrid cols={{ base: 1, xs: 2, lg: 3 }} spacing="md">
          {picks.slice(0, 6).map((p) => <PlayerCard key={p.player_id} player={p} />)}
        </SimpleGrid>
        <Anchor component={Link} to="/players?verdict=pick&sort=value_for_money" c="turf.4" mt="md" display="inline-block">
          See all {picks.length} value picks →
        </Anchor>
      </Section>

      <Section title="The season in numbers">
        <Grid gutter="lg">
          <Grid.Col span={{ base: 12, lg: 6 }}>
            <Card h="100%">
              <Text fw={700} size="lg">Most valuable squads</Text>
              <Text size="sm" c="dimmed" mb="md">Total market value of each squad. Click a bar to see that club&apos;s players.</Text>
              <SquadValueChart clubs={clubs} />
            </Card>
          </Grid.Col>
          <Grid.Col span={{ base: 12, lg: 6 }}>
            <Stack gap="lg" h="100%">
              <Card>
                <Text fw={700} size="lg">What players cost</Text>
                <Text size="sm" c="dimmed" mb="md">
                  {Math.round((players.filter((p) => p.market_value_eur < 20e6).length / players.length) * 100)}% of
                  players are valued under €20M; only {players.filter((p) => p.market_value_eur >= 80e6).length} are
                  worth €80M or more.
                </Text>
                <PriceDistributionChart players={players} />
              </Card>
              <Card style={{ flex: 1 }}>
                <Text fw={700} size="lg" mb="xs">How to read a player&apos;s price verdict</Text>
                <List spacing={6} size="sm">
                  <List.Item><b>Value pick:</b> a strong regular whose stats point to a clearly higher price.</List.Item>
                  <List.Item><b>Stats say worth more:</b> estimate at least 20% above market value.</List.Item>
                  <List.Item><b>Fair price:</b> estimate within 20% of market value.</List.Item>
                  <List.Item><b>Priced above stats:</b> our estimate is at least 20% below market value, often because of reputation or potential.</List.Item>
                  <List.Item><b>Not enough minutes:</b> under 900 minutes, too few to judge.</List.Item>
                </List>
              </Card>
            </Stack>
          </Grid.Col>
          <Grid.Col span={12}>
            <Card>
              <Text fw={700} size="lg">Stats vs price</Text>
              <Text size="sm" c="dimmed" mb="md">
                Each dot is a player. Dots above the diagonal line have stats that point to a higher price than the
                market pays; dots below cost more than their stats suggest. Click a dot to open that player.
              </Text>
              <StatsVsPriceChart players={players} />
            </Card>
          </Grid.Col>
        </Grid>
      </Section>

      <Section title="How it works">
        <SimpleGrid cols={{ base: 1, sm: 2, lg: 4 }} spacing="md">
          {STEPS.map(([title, text], i) => (
            <Card key={title}>
              <ThemeIcon radius="xl" size={32} variant="light" mb="sm">{i + 1}</ThemeIcon>
              <Text fw={700} mb={4}>{title}</Text>
              <Text size="sm" c="dimmed">{text}</Text>
            </Card>
          ))}
        </SimpleGrid>
      </Section>

      {check && (
        <Section title="Does it actually work? We checked."
          intro="Our estimates were made in June 2026, before the summer transfer window. So we compared them with the fees clubs actually paid for the players who moved.">
          <Card>
            <SimpleGrid cols={{ base: 1, md: 3 }} spacing="lg" mb="md">
              <div>
                <Text fw={800} size="28px">{check.n_deals}</Text>
                <Text size="sm" c="dimmed">players sold this summer for a reported fee</Text>
              </div>
              <div>
                <Text fw={800} size="28px">{check.median_fee_over_valuation.toFixed(2)}×</Text>
                <Text size="sm" c="dimmed">typical fee compared with the player&apos;s market value (clubs usually pay a premium)</Text>
              </div>
              <div>
                <Text fw={800} size="28px" c="orange.4">Not yet</Text>
                <Text size="sm" c="dimmed">did our &quot;worth more&quot; calls sell for bigger premiums</Text>
              </div>
            </SimpleGrid>
            <Text>
              Honest answer: the model is good at telling the best players from the rest, but it couldn&apos;t beat
              the market. Market values predicted the actual fees better than our estimates did, and players we
              flagged as worth more didn&apos;t sell for bigger premiums than anyone else. Forty transfers is a small
              sample, and fees also depend on contracts and negotiations, so treat value picks as players worth a
              closer look, not guaranteed bargains.
            </Text>
          </Card>
        </Section>
      )}

      {sources.length > 0 && (
        <Section title="Where the data comes from">
          <Card padding={0}>
            <div style={{ overflowX: 'auto' }}>
              <Table verticalSpacing="sm" horizontalSpacing="md">
                <Table.Thead>
                  <Table.Tr>
                    <Table.Th>Source</Table.Th><Table.Th>Covers</Table.Th><Table.Th>How recent</Table.Th><Table.Th>Used for</Table.Th>
                  </Table.Tr>
                </Table.Thead>
                <Table.Tbody>
                  {sources.map((s) => (
                    <Table.Tr key={s.name}>
                      <Table.Td fw={600}>{s.name}</Table.Td>
                      <Table.Td>{s.scope}</Table.Td>
                      <Table.Td>{s.coverage}</Table.Td>
                      <Table.Td c="dimmed">{s.used_for}</Table.Td>
                    </Table.Tr>
                  ))}
                </Table.Tbody>
              </Table>
            </div>
          </Card>
        </Section>
      )}

      <Section title="About the project">
        <Card>
          <Text mb="sm">
            Prem Scout is a fan-made project by{' '}
            <Anchor href="https://github.com/arnavt16" c="turf.4">Arnav Thorat</Anchor>. It looks back at the 2025–26
            Premier League season and asks a simple question: do players&apos; prices match how they actually played?
          </Text>
          <Text size="sm" c="dimmed">
            Under the hood: Python and scikit-learn for the model, FastAPI for the data, and React for this site.
            Market values aren&apos;t transfer fees or asking prices, and the site doesn&apos;t know about injuries,
            wages or contracts.
          </Text>
        </Card>
      </Section>
    </Stack>
  );
}
