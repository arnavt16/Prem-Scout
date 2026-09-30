import { Link, useParams } from 'react-router-dom';
import { PolarAngleAxis, PolarGrid, Radar, RadarChart, ResponsiveContainer, Tooltip } from 'recharts';
import { Alert, Anchor, Badge, Card, Grid, Group, SimpleGrid, Stack, Table, Text, Title } from '@mantine/core';
import { ClubBadge } from '../components/ClubBadge';
import { ExplanationCard } from '../components/ExplanationCard';
import { LoadingState } from '../components/LoadingState';
import { SimilarPlayersCard } from '../components/SimilarPlayersCard';
import { VerdictBadge } from '../components/VerdictBadge';
import { useFetch } from '../hooks/useFetch';
import { api } from '../services/api';
import { CHART, tooltipStyle } from '../utils/chartColors';
import { clubInfo } from '../utils/clubs';
import { formatEur, formatPct } from '../utils/format';
import { positionLabel, verdictKey, verdictSentence } from '../utils/player';

const num = (v, digits = 2) => (v == null ? '—' : Number(v).toFixed(digits));

function Money({ label, value, color, hint }) {
  return (
    <Card padding="md">
      <Text size="sm" c="dimmed">{label}</Text>
      <Text fw={800} size="28px" c={color}>{value}</Text>
      {hint && <Text size="xs" c="dimmed">{hint}</Text>}
    </Card>
  );
}

function StatGroup({ title, rows }) {
  const visible = rows.filter(([, v]) => v != null && v !== '—');
  if (!visible.length) return null;
  return (
    <div>
      <Text size="xs" fw={700} c="dimmed" tt="uppercase" mb={6} style={{ letterSpacing: 0.6 }}>{title}</Text>
      <Table>
        <Table.Tbody>
          {visible.map(([label, value]) => (
            <Table.Tr key={label}>
              <Table.Td c="dimmed">{label}</Table.Td>
              <Table.Td ta="right" fw={600}>{value}</Table.Td>
            </Table.Tr>
          ))}
        </Table.Tbody>
      </Table>
    </div>
  );
}

function statGroups(p) {
  if (p.position_group === 'GK') {
    return [
      ['Goalkeeping', [
        ['Goals conceded per 90', num(p.goals_against_per90)],
        ['Save percentage', formatPct(p.save_pct, { showSign: false })],
        ['Clean sheet rate', formatPct(p.clean_sheet_pct, { showSign: false })],
        ['Penalties saved', p.penalty_saves],
      ]],
      ['Playing time', [
        ['Minutes', p.minutes.toLocaleString()], ['Starts', p.starts],
        ['Match rating', num(p.rating)], ['Pass accuracy', formatPct(p.pass_completion_pct, { showSign: false })],
      ]],
    ];
  }
  return [
    ['Scoring', [
      ['Goals', p.goals], ['Expected goals (xG)', num(p.xg, 1)], ['Shots per 90', num(p.shots_per90)],
      ['Shot accuracy', formatPct(p.shot_on_target_pct, { showSign: false })],
    ]],
    ['Creating', [
      ['Assists', p.assists], ['Expected assists (xA)', num(p.xa, 1)], ['Key passes', p.key_passes],
      ['Big chances created', p.big_chances_created], ['Successful dribbles', p.successful_dribbles],
    ]],
    ['Passing & defending', [
      ['Pass accuracy', formatPct(p.pass_completion_pct, { showSign: false })],
      ['Final-third passes per 90', num(p.final_third_passes_per90, 1)],
      ['Tackles won per 90', num(p.tackles_won_per90)], ['Interceptions per 90', num(p.interceptions_per90)],
      ['Aerial duels won', formatPct(p.aerial_win_pct, { showSign: false })],
    ]],
    ['Playing time', [
      ['Minutes', p.minutes.toLocaleString()], ['Starts', p.starts], ['Match rating', num(p.rating)],
      ['Yellow / red cards', `${p.yellow_cards} / ${p.red_cards}`],
    ]],
  ];
}

export function PlayerProfile() {
  const { id } = useParams();
  const { data: player, error, loading } = useFetch(() => api.getPlayer(id), [id]);
  // Explanations and similar players exist only for players with enough
  // minutes for an estimate; skip the requests (and their 404s) otherwise.
  const hasModelData = player?.meets_minutes_threshold ?? false;
  const { data: explanation } = useFetch(
    () => (hasModelData ? api.getPlayerExplanation(id) : Promise.resolve(null)), [id, hasModelData]);
  const { data: similar } = useFetch(
    () => (hasModelData ? api.getSimilarPlayers(id) : Promise.resolve(null)), [id, hasModelData]);

  if (loading) return <LoadingState />;
  if (error) {
    return (
      <Alert color="red" title="Player not found">
        {error === 'Not found' ? `No player with id ${id}` : error}. <Anchor component={Link} to="/players">Back to the player database</Anchor>
      </Alert>
    );
  }

  const p = player;
  const club = clubInfo(p.club);
  const pos = positionLabel(p.position_group);
  const diff = p.estimated_market_value_eur == null ? null : p.estimated_market_value_eur - p.market_value_eur;
  const radarData = p.radar.map((r) => ({ category: r.label, percentile: r.percentile ?? 0 }));
  const unrated = verdictKey(p) === 'unrated';

  return (
    <Stack gap="lg">
      <Anchor component={Link} to={`/players?club=${encodeURIComponent(p.club)}`} size="sm" c="dimmed">
        ← {club.display} players
      </Anchor>

      <Group gap="lg" wrap="nowrap" align="center">
        <ClubBadge club={p.club} size={72} />
        <div style={{ minWidth: 0 }}>
          <Title order={1}>{p.name}</Title>
          <Text c="dimmed" size="lg">{club.display} · {p.sub_position} · Age {Math.round(p.age)}</Text>
          <Group gap={8} mt={6}><VerdictBadge player={p} size="lg" /></Group>
        </div>
      </Group>

      <SimpleGrid cols={{ base: 1, sm: 3 }}>
        <Money label="Market value" value={formatEur(p.market_value_eur)} hint={`Transfermarkt, ${p.valuation_date.slice(0, 10)}`} />
        <Money label="Our estimate" value={formatEur(p.estimated_market_value_eur)} color="turf.4"
          hint={unrated ? 'Needs 900+ minutes' : 'From stats, age, minutes and team strength'} />
        <Money label="Difference" value={diff == null ? '—' : `${diff > 0 ? '+' : ''}${formatEur(diff)}`}
          color={diff == null ? undefined : diff > 0 ? 'turf.4' : 'orange.4'}
          hint={diff == null ? undefined : diff > 0 ? 'Stats point higher than the market' : 'Market pays more than stats suggest'} />
      </SimpleGrid>

      <Card>
        <Text fw={700} size="lg" mb={6}>Our verdict</Text>
        <Text>{verdictSentence(p)}</Text>
        {p.performance_percentile != null && (
          <Text size="sm" c="dimmed" mt="sm">
            Output this season: better than {Math.round(p.performance_percentile)}% of Premier League {pos.toLowerCase()}s
            with at least 900 minutes.
          </Text>
        )}
      </Card>

      <Grid gutter="lg">
        <Grid.Col span={{ base: 12, md: 5 }}>
          <Card h="100%">
            <Text fw={700} size="lg" mb={4}>Compared with other {pos.toLowerCase()}s</Text>
            <Text size="sm" c="dimmed" mb="sm">
              Further out means better than more of them. 50 is average for the position.
            </Text>
            <ResponsiveContainer width="100%" height={300}>
              <RadarChart data={radarData} outerRadius="72%">
                <PolarGrid stroke={CHART.grid} />
                <PolarAngleAxis dataKey="category" tick={{ fill: CHART.axis, fontSize: 11 }} />
                <Tooltip {...tooltipStyle} formatter={(v) => [`Better than ${Math.round(v)}%`, 'Rank']} />
                <Radar dataKey="percentile" stroke={CHART.valuePick} strokeWidth={2} fill={CHART.valuePick} fillOpacity={0.3} />
              </RadarChart>
            </ResponsiveContainer>
          </Card>
        </Grid.Col>
        <Grid.Col span={{ base: 12, md: 7 }}>
          <Card h="100%">
            <Text fw={700} size="lg" mb="md">Season stats</Text>
            <SimpleGrid cols={{ base: 1, sm: 2 }} spacing="lg">
              {statGroups(p).map(([title, rows]) => <StatGroup key={title} title={title} rows={rows} />)}
            </SimpleGrid>
            {p.sofascore_minutes != null && (
              <Text size="xs" c="dimmed" mt="md">
                Match rating, xG, xA, passing and duel stats come from SofaScore (up to matchday 35). Other stats cover the full season.
              </Text>
            )}
          </Card>
        </Grid.Col>
      </Grid>

      {(explanation || similar?.length > 0) && (
        <Grid gutter="lg">
          {explanation && (
            <Grid.Col span={{ base: 12, md: 7 }}>
              <ExplanationCard explanation={explanation} />
            </Grid.Col>
          )}
          {similar?.length > 0 && (
            <Grid.Col span={{ base: 12, md: 5 }}>
              <SimilarPlayersCard players={similar} positionLabel={pos} />
            </Grid.Col>
          )}
        </Grid>
      )}
      {!unrated && p.position_group === 'GK' && (
        <Badge variant="light" color="gray" w="fit-content">Goalkeeper estimates are rougher than outfield ones</Badge>
      )}
    </Stack>
  );
}
