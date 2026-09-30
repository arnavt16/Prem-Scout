// Validated dark-mode data palette (reference categorical slots 1 and 3,
// checked against the #151b23 card surface: contrast >= 3:1, CVD-separable).
export const CHART = {
  series1: '#3987e5',
  valuePick: '#199e70',
  grid: '#2d3743',
  axis: '#8b96a3',
  surface: '#151b23',
};

export const tooltipStyle = {
  contentStyle: {
    background: '#0d1117', border: '1px solid #2d3743', borderRadius: 8, color: '#e6edf3', fontSize: 13,
  },
  labelStyle: { color: '#e6edf3', fontWeight: 600 },
  itemStyle: { color: '#b8c2cc' },
  cursor: { fill: 'rgba(255,255,255,0.04)' },
};
