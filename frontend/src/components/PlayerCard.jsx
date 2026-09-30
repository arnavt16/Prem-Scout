import { Link } from 'react-router-dom';
import { Card, Group, Stack, Text } from '@mantine/core';
import { ClubBadge } from './ClubBadge';
import { VerdictBadge } from './VerdictBadge';
import { clubInfo } from '../utils/clubs';
import { formatEur, plural } from '../utils/format';
import { positionLabel } from '../utils/player';

function Figure({ label, value, accent }) {
  return (
    <div>
      <Text size="xs" c="dimmed">{label}</Text>
      <Text fw={700} size="lg" c={accent ? 'turf.4' : undefined}>{value}</Text>
    </div>
  );
}

export function PlayerCard({ player: p }) {
  const isGk = p.position_group === 'GK';
  return (
    <Card component={Link} to={`/players/${p.player_id}`} className="hover-card" padding="md">
      <Group wrap="nowrap" gap="sm" mb="sm">
        <ClubBadge club={p.club} size={36} />
        <div style={{ minWidth: 0 }}>
          <Text fw={700} truncate>{p.name}</Text>
          <Text size="xs" c="dimmed" truncate>
            {clubInfo(p.club).display} · {positionLabel(p.position_group)} · {Math.round(p.age)}
          </Text>
        </div>
      </Group>
      <Group grow mb="sm" align="flex-start">
        <Figure label="Market value" value={formatEur(p.market_value_eur)} />
        <Figure label="Our estimate" value={formatEur(p.estimated_market_value_eur)} accent />
      </Group>
      <Stack gap={6}>
        <VerdictBadge player={p} />
        <Text size="xs" c="dimmed">
          {isGk
            ? `${p.minutes.toLocaleString()} min`
            : `${plural(p.goals, 'goal')} · ${plural(p.assists, 'assist')} · ${p.minutes.toLocaleString()} min`}
          {p.rating != null && ` · rating ${p.rating.toFixed(2)}`}
        </Text>
      </Stack>
    </Card>
  );
}
