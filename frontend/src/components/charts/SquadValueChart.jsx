import { useNavigate } from 'react-router-dom';
import { Bar, BarChart, CartesianGrid, LabelList, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts';
import { CHART, tooltipStyle } from '../../utils/chartColors';
import { formatEur } from '../../utils/format';

/** Total market value per club, largest first. Clicking a bar opens that club. */
export function SquadValueChart({ clubs }) {
  const navigate = useNavigate();
  const data = [...clubs].sort((a, b) => b.value - a.value);
  return (
    <ResponsiveContainer width="100%" height={data.length * 26 + 30}>
      <BarChart data={data} layout="vertical" margin={{ left: 8, right: 56, top: 4, bottom: 4 }} barCategoryGap={4}>
        <CartesianGrid horizontal={false} stroke={CHART.grid} />
        <XAxis type="number" tickFormatter={(v) => formatEur(v)} tick={{ fill: CHART.axis, fontSize: 11 }}
          axisLine={false} tickLine={false} />
        <YAxis type="category" dataKey="display" width={130} tick={{ fill: CHART.axis, fontSize: 12 }}
          axisLine={false} tickLine={false} />
        <Tooltip {...tooltipStyle} formatter={(v) => [formatEur(v), 'Squad market value']} />
        <Bar dataKey="value" fill={CHART.series1} barSize={18} radius={[0, 4, 4, 0]} cursor="pointer"
          onClick={(d) => navigate(`/players?club=${encodeURIComponent(d.name)}`)}>
          <LabelList dataKey="value" position="right" formatter={(v) => formatEur(v)}
            style={{ fill: '#b8c2cc', fontSize: 11 }} />
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}
