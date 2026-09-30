import { Button, Card, Chip, Group, RangeSlider, Select, Stack, Switch, Text, TextInput } from '@mantine/core';
import { CLUBS } from '../utils/clubs';
import { DEFAULT_FILTERS, SORT_OPTIONS } from '../utils/filters';
import { POSITIONS, VERDICTS } from '../utils/player';

function Section({ title, children }) {
  return (
    <div>
      <Text size="xs" fw={700} c="dimmed" tt="uppercase" mb={8} style={{ letterSpacing: 0.6 }}>{title}</Text>
      {children}
    </div>
  );
}

export function FilterSidebar({ filters, onChange, sticky = false }) {
  const set = (key) => (value) => onChange({ ...filters, [key]: value });
  return (
    <Card padding="md" style={sticky ? { position: 'sticky', top: 84 } : undefined}>
      <Stack gap="lg">
        <TextInput placeholder="Search a player" value={filters.search}
          onChange={(e) => set('search')(e.currentTarget.value)} aria-label="Search a player" />
        <Section title="Sort by">
          <Select data={SORT_OPTIONS} value={filters.sort} onChange={(v) => set('sort')(v ?? 'market_value_eur')}
            allowDeselect={false} aria-label="Sort by" />
        </Section>
        <Section title="Club">
          <Select placeholder="All clubs" clearable searchable value={filters.club} onChange={set('club')}
            data={CLUBS.map((c) => ({ value: c.name, label: c.display }))} aria-label="Club" />
        </Section>
        <Section title="Position">
          <Chip.Group value={filters.position} onChange={set('position')}>
            <Group gap={6}>
              <Chip value="all" size="xs">All</Chip>
              {Object.entries(POSITIONS).map(([code, p]) => (
                <Chip key={code} value={code} size="xs">{p.plural}</Chip>
              ))}
            </Group>
          </Chip.Group>
        </Section>
        <Section title={`Age: ${filters.age[0]} to ${filters.age[1]}`}>
          <RangeSlider min={15} max={40} minRange={1} value={filters.age} onChange={set('age')} label={null} />
        </Section>
        <Section title={`Market value: €${filters.value[0]}M to €${filters.value[1]}M${filters.value[1] === 200 ? '+' : ''}`}>
          <RangeSlider min={0} max={200} step={5} minRange={5} value={filters.value} onChange={set('value')} label={null} />
        </Section>
        <Section title="Price verdict">
          <Chip.Group multiple value={filters.verdicts} onChange={set('verdicts')}>
            <Group gap={6}>
              {Object.entries(VERDICTS).map(([key, v]) => (
                <Chip key={key} value={key} size="xs" color={v.color}>{v.label}</Chip>
              ))}
            </Group>
          </Chip.Group>
        </Section>
        <Switch label="Regular starters only (1,800+ minutes)" checked={filters.regularsOnly}
          onChange={(e) => set('regularsOnly')(e.currentTarget.checked)} />
        <Button variant="subtle" color="gray" onClick={() => onChange(DEFAULT_FILTERS)}>Reset filters</Button>
      </Stack>
    </Card>
  );
}
