import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { CHART, tooltipStyle } from '../../utils/chartColors';

const EDGES = [0, 5, 10, 20, 40, 80, Infinity];

function bucketLabel(lo, hi) {
  if (lo === 0) return `Under €${hi}M`;
  return hi === Infinity ? `€${lo}M+` : `€${lo} to ${hi}M`;
}

/** How many players fall into each market-value band. */
export function PriceDistributionChart({ players }) {
  const data = EDGES.slice(0, -1).map((lo, i) => ({
    band: bucketLabel(lo, EDGES[i + 1]),
    players: players.filter((p) => p.market_value_eur / 1e6 >= lo && p.market_value_eur / 1e6 < EDGES[i + 1]).length,
  }));
  return (
    <ResponsiveContainer width="100%" height={260}>
      <BarChart data={data} margin={{ top: 8, right: 8, left: -12, bottom: 0 }}>
        <CartesianGrid vertical={false} stroke={CHART.grid} />
        <XAxis dataKey="band" tick={{ fill: CHART.axis, fontSize: 12 }} axisLine={false} tickLine={false} />
        <YAxis allowDecimals={false} tick={{ fill: CHART.axis, fontSize: 12 }} axisLine={false} tickLine={false} />
        <Tooltip {...tooltipStyle} formatter={(v) => [v, 'Players']} />
        <Bar dataKey="players" fill={CHART.series1} barSize={24} radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}
