import { Badge } from '@mantine/core';
import { verdict } from '../utils/player';

export function VerdictBadge({ player, size = 'sm' }) {
  const v = verdict(player);
  return (
    <Badge color={v.color} variant={v.key === 'pick' ? 'filled' : 'light'} size={size} radius="sm">
      {v.label}
    </Badge>
  );
}
