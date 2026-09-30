import { useNavigate } from 'react-router-dom';
import {
  CartesianGrid, Legend, ReferenceLine, ResponsiveContainer, Scatter, ScatterChart, Tooltip, XAxis, YAxis,
} from 'recharts';
import { Text } from '@mantine/core';
import { CHART } from '../../utils/chartColors';
import { formatEur } from '../../utils/format';

const TICKS = [1e6, 3e6, 10e6, 30e6, 100e6];
const DOMAIN = [5e5, 2.2e8];

// Dots carry a 2px surface-coloured ring so overlapping points stay separable.
const dot = (radius, fill, opacity) => function Dot({ cx, cy }) {
  return <circle cx={cx} cy={cy} r={radius} fill={fill} fillOpacity={opacity} stroke={CHART.surface} strokeWidth={2} />;
};
const OtherDot = dot(4, CHART.series1, 0.75);
const PickDot = dot(6, CHART.valuePick, 1);

function PointTooltip({ active, payload }) {
  if (!active || !payload?.length) return null;
  const p = payload[0].payload;
  return (
    <div style={{ background: '#0d1117', border: '1px solid #2d3743', borderRadius: 8, padding: '8px 10px' }}>
      <Text size="sm" fw={700}>{p.name}</Text>
      <Text size="xs" c="dimmed">{p.club}</Text>
      <Text size="xs" mt={4}>Market value {formatEur(p.market)}</Text>
      <Text size="xs">Our estimate {formatEur(p.estimate)}</Text>
    </div>
  );
}

/**
 * Market value (x) against the model's estimate (y), log scales. Points above
 * the diagonal are players whose stats point to a higher price.
 */
export function StatsVsPriceChart({ players }) {
  const navigate = useNavigate();
  const rated = players.filter((p) => p.estimated_market_value_eur != null)
    .map((p) => ({ id: p.player_id, name: p.name, club: p.club, market: p.market_value_eur,
      estimate: Math.max(p.estimated_market_value_eur, DOMAIN[0]), pick: p.eligible_for_ranking }));
  const open = (d) => navigate(`/players/${d.id}`);
  return (
    <ResponsiveContainer width="100%" height={380}>
      <ScatterChart margin={{ top: 8, right: 16, bottom: 28, left: 8 }}>
        <CartesianGrid stroke={CHART.grid} />
        <XAxis type="number" dataKey="market" scale="log" domain={DOMAIN} ticks={TICKS} tickFormatter={formatEur}
          tick={{ fill: CHART.axis, fontSize: 11 }} axisLine={false} tickLine={false}
          label={{ value: 'Market value', position: 'bottom', offset: 8, fill: CHART.axis, fontSize: 12 }} />
        <YAxis type="number" dataKey="estimate" scale="log" domain={DOMAIN} ticks={TICKS} tickFormatter={formatEur}
          tick={{ fill: CHART.axis, fontSize: 11 }} axisLine={false} tickLine={false} width={56}
          label={{ value: 'Our estimate', angle: -90, position: 'insideLeft', fill: CHART.axis, fontSize: 12 }} />
        <ReferenceLine segment={[{ x: DOMAIN[0], y: DOMAIN[0] }, { x: DOMAIN[1], y: DOMAIN[1] }]}
          stroke={CHART.axis} strokeWidth={1}
          label={{ value: 'Fair price', position: 'insideTopLeft', fill: CHART.axis, fontSize: 11 }} />
        <Tooltip content={<PointTooltip />} cursor={false} />
        <Legend verticalAlign="top" height={28} wrapperStyle={{ fontSize: 12, color: '#b8c2cc' }} />
        <Scatter name="Other players" data={rated.filter((d) => !d.pick)} fill={CHART.series1}
          shape={OtherDot} cursor="pointer" onClick={open} />
        <Scatter name="Value picks" data={rated.filter((d) => d.pick)} fill={CHART.valuePick}
          shape={PickDot} cursor="pointer" onClick={open} />
      </ScatterChart>
    </ResponsiveContainer>
  );
}
