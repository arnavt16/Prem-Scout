import { Link } from 'react-router-dom';
import { Badge, Card, Group, Stack, Text } from '@mantine/core';
import { ClubBadge } from './ClubBadge';
import { clubInfo } from '../utils/clubs';
import { formatEur } from '../utils/format';

export function SimilarPlayersCard({ players, positionLabel }) {
  return (
    <Card>
      <Text fw={700} size="lg" mb={4}>Plays like</Text>
      <Text size="sm" c="dimmed" mb="md">
        {positionLabel}s with the most similar style this season, based on what they do per 90 minutes. Price
        isn&apos;t considered, so cheaper alternatives can show up.
      </Text>
      <Stack gap="xs">
        {players.map((p) => (
          <Card key={p.player_id} component={Link} to={`/players/${p.player_id}`} className="hover-card"
            padding="sm" bg="dark.7">
            <Group justify="space-between" wrap="nowrap">
              <Group gap="sm" wrap="nowrap" style={{ minWidth: 0 }}>
                <ClubBadge club={p.club} size={28} />
                <div style={{ minWidth: 0 }}>
                  <Text fw={600} size="sm" truncate>{p.name}</Text>
                  <Text size="xs" c="dimmed" truncate>{clubInfo(p.club).display} · {formatEur(p.market_value_eur)}</Text>
                </div>
              </Group>
              <Text fw={700} c="turf.4" size="sm">{Math.round(Math.max(p.similarity, 0) * 100)}% match</Text>
            </Group>
            {p.shared_traits.length > 0 && (
              <Group gap={4} mt={6}>
                {p.shared_traits.map((t) => (
                  <Badge key={t} size="xs" variant="light" color="gray">{t.replace(' per 90', '')}</Badge>
                ))}
              </Group>
            )}
          </Card>
        ))}
      </Stack>
    </Card>
  );
}
