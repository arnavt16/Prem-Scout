import { Card, Grid, Group, Progress, Stack, Text } from '@mantine/core';
import { formatEur } from '../utils/format';

// Contributions are in log-value units; exp(impact) - 1 is the rough
// percentage that factor moved the estimate, which reads far better.
const pct = (impact) => Math.round((Math.exp(impact) - 1) * 100);

function Factor({ c, max }) {
  const up = c.impact >= 0;
  return (
    <div>
      <Group justify="space-between" mb={4} wrap="nowrap">
        <Text size="sm">{c.group}</Text>
        {/* The column heading says up or down, so no plus or minus sign is needed. */}
        <Text size="sm" fw={700} c={up ? 'turf.4' : 'orange.4'}>{Math.abs(pct(c.impact))}%</Text>
      </Group>
      <Progress value={(Math.abs(c.impact) / max) * 100} color={up ? 'turf' : 'orange'} size="sm"
        aria-label={`${c.group} ${up ? 'raised' : 'lowered'} the estimate`} />
    </div>
  );
}

export function ExplanationCard({ explanation }) {
  // Themes smaller than about 1% are noise to a reader.
  const groups = explanation.groups.filter((g) => Math.abs(g.impact) >= 0.01);
  const max = Math.max(...groups.map((g) => Math.abs(g.impact)), 1e-9);
  const ups = groups.filter((g) => g.impact > 0).slice(0, 5);
  const downs = groups.filter((g) => g.impact < 0).slice(0, 5);
  return (
    <Card>
      <Text fw={700} size="lg" mb={4}>Why this estimate?</Text>
      <Text size="sm" c="dimmed" mb="lg">
        The model starts from a typical player (about {formatEur(explanation.base_value_eur)}) and adjusts for each
        part of their game. These are the biggest effects, ending at {formatEur(explanation.predicted_value_eur)}. The model
        never saw this player&apos;s own price while learning.
      </Text>
      <Grid gutter="xl">
        <Grid.Col span={{ base: 12, sm: 6 }}>
          <Text size="sm" fw={700} c="turf.4" mb="sm">Pushed the price up</Text>
          <Stack gap="sm">
            {ups.length ? ups.map((c) => <Factor key={c.group} c={c} max={max} />) : <Text size="sm" c="dimmed">Nothing major.</Text>}
          </Stack>
        </Grid.Col>
        <Grid.Col span={{ base: 12, sm: 6 }}>
          <Text size="sm" fw={700} c="orange.4" mb="sm">Pulled the price down</Text>
          <Stack gap="sm">
            {downs.length ? downs.map((c) => <Factor key={c.group} c={c} max={max} />) : <Text size="sm" c="dimmed">Nothing major.</Text>}
          </Stack>
        </Grid.Col>
      </Grid>
    </Card>
  );
}
