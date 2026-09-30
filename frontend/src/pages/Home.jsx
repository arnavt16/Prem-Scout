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
  ['Collect the season', 'Stats for every Premier League player from 2025/26: goals, expected goals, passing, dribbling, defending and match ratings, plus each player\'s Transfermarkt market value.'],
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
        <Text c="turf.4" fw={700} tt="uppercase" size="sm" style={{ letterSpacing: 1 }}>2025/26 Premier League</Text>
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
        <Fact value={typicalError ? `±${formatEur(typicalError)}` : 'N/A'} label="typical gap between our estimate and market value" />
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
        <Section title="Did players sell for more than their market value?"
          intro={`Our estimates were made in June 2026, before the summer transfer window opened. ${check.n_deals} of these players then moved for a reported fee, so we compared what clubs actually paid with each player's market value.`}>
          <Card>
            <SimpleGrid cols={{ base: 1, md: 3 }} spacing="lg" mb="lg">
              <div>
                <Text fw={800} size="32px" c="turf.4">{check.n_sold_above_value} of {check.n_deals}</Text>
                <Text size="sm" c="dimmed">sold for more than their market value</Text>
              </div>
              <div>
                <Text fw={800} size="32px" c="turf.4">
                  {Math.round((check.total_fees_eur / check.total_market_value_eur - 1) * 100)}% more
                </Text>
                <Text size="sm" c="dimmed">
                  paid in total: {formatEur(check.total_fees_eur)} for players valued at {formatEur(check.total_market_value_eur)}
                </Text>
              </div>
              <div>
                <Text fw={800} size="32px" c="turf.4">
                  {formatEur(check.top_quarter_by_estimate.median_fee_eur)}
                </Text>
                <Text size="sm" c="dimmed">
                  typical fee for the {check.top_quarter_by_estimate.n} players our model rated highest, against{' '}
                  {formatEur(check.top_quarter_by_estimate.rest_median_fee_eur)} for the rest
                </Text>
              </div>
            </SimpleGrid>
            <Stack gap="sm">
              <Text>
                <b>Transfer fees run well ahead of market values.</b>{' '}
                {Math.round((check.n_sold_above_value / check.n_deals) * 100)}% of these players went for more than
                their listed value, and {check.n_sold_25pct_above_value} of the {check.n_deals} went for at least
                25% more. That&apos;s how inflated the transfer market is: a market value is closer to a starting
                point than a price tag, and clubs routinely pay a premium on top.
              </Text>
              <Text>
                <b>The model is useful for sizing players up.</b> Using only stats, age, minutes and team strength,
                it picked out the players clubs paid the most for: the {check.top_quarter_by_estimate.n} it rated
                highest sold for about{' '}
                {Math.round(check.top_quarter_by_estimate.median_fee_eur / check.top_quarter_by_estimate.rest_median_fee_eur * 10) / 10}
                {' '}times as much as the rest. That makes it a good second opinion on what a player&apos;s season
                is really worth.
              </Text>
              <Text size="sm" c="dimmed">
                What it can&apos;t do yet is predict which players will sell above their market value. Players it
                rated as worth more beat their market value {check.sold_above_value_by_model_call.model_said_undervalued.sold_above}{' '}
                times out of {check.sold_above_value_by_model_call.model_said_undervalued.n}, about as often as
                everyone else ({check.sold_above_value_by_model_call.model_said_overvalued.sold_above} out of{' '}
                {check.sold_above_value_by_model_call.model_said_overvalued.n}). So treat value picks as players
                worth a closer look rather than guaranteed bargains.
              </Text>
            </Stack>
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
            Prem Scout is a fan project by{' '}
            <Anchor href="https://github.com/arnavt16" c="turf.4">Arnav Thorat</Anchor>. It looks back at the 2025/26
            Premier League season and asks a simple question: do players&apos; prices match how they actually played?
          </Text>
          <Text size="sm" c="dimmed">
            Under the hood: Python for the model, FastAPI for the data, and React for this site.
            Market values aren&apos;t transfer fees or asking prices, and the site doesn&apos;t know about injuries,
            wages or contracts.
          </Text>
        </Card>
      </Section>
    </Stack>
  );
}
