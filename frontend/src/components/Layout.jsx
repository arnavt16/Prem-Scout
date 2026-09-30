import { NavLink as RouterNavLink, Link, Outlet } from 'react-router-dom';
import { Anchor, Group, Text } from '@mantine/core';

const links = [
  { to: '/', label: 'Home' },
  { to: '/players', label: 'Player database' },
];

export function Layout() {
  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      <header
        style={{
          position: 'sticky', top: 0, zIndex: 10,
          background: 'rgba(13, 17, 23, 0.92)', backdropFilter: 'blur(8px)',
          borderBottom: '1px solid var(--mantine-color-dark-4)',
          padding: '12px clamp(16px, 4vw, 32px)',
        }}
      >
        <Group justify="space-between" maw={1320} mx="auto" wrap="nowrap">
          <Link to="/" style={{ textDecoration: 'none' }}>
            <Text fw={800} size="xl" style={{ letterSpacing: -0.5 }}>
              Prem <Text span inherit c="turf.4">Scout</Text>
            </Text>
          </Link>
          <Group gap="lg" wrap="nowrap">
            {links.map((link) => (
              <RouterNavLink
                key={link.to}
                to={link.to}
                end={link.to === '/'}
                style={({ isActive }) => ({
                  fontSize: 15,
                  fontWeight: isActive ? 700 : 500,
                  color: isActive ? 'var(--mantine-color-turf-4)' : 'var(--mantine-color-dark-1)',
                  textDecoration: 'none',
                  whiteSpace: 'nowrap',
                })}
              >
                {link.label}
              </RouterNavLink>
            ))}
          </Group>
        </Group>
      </header>
      <main style={{ flex: 1, width: '100%', maxWidth: 1320, margin: '0 auto', padding: '32px clamp(16px, 4vw, 32px)' }}>
        <Outlet />
      </main>
      <footer style={{ borderTop: '1px solid var(--mantine-color-dark-4)', padding: '20px clamp(16px, 4vw, 32px)' }}>
        <Group justify="space-between" maw={1320} mx="auto">
          <Text size="sm" c="dimmed">
            Built by{' '}
            <Anchor href="https://github.com/arnavt16" c="turf.4" underline="hover">Arnav Thorat</Anchor>
            {' '}· 2025/26 Premier League season
          </Text>
          <Text size="xs" c="dimmed">
            A fan project. Not affiliated with the Premier League or any club. Crests belong to their clubs.
          </Text>
        </Group>
      </footer>
    </div>
  );
}
