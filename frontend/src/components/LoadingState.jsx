import { Loader, Stack, Text } from '@mantine/core';

export function LoadingState() {
  return (
    <Stack align="center" gap="sm" py="xl" role="status" aria-live="polite">
      <Loader />
      <Text fw={500}>Loading scouting data…</Text>
    </Stack>
  );
}
