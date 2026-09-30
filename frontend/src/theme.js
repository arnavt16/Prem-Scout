import { createTheme } from '@mantine/core';

// Dark-only theme. "turf" (aqua-green) is the brand accent and the colour
// of value picks; chart series use the validated dark data palette in
// utils/chartColors.js rather than theme colours.
const turf = [
  '#e3f7ef', '#c3ecdb', '#9ddfc4', '#72d0aa', '#4cc294',
  '#2fb383', '#199e70', '#12825c', '#0d6547', '#084733',
];

// Mantine's dark scale, re-stepped to a cool near-black: [0] is body text,
// [6] the card surface, [7] the page background.
const dark = [
  '#e6edf3', '#b8c2cc', '#8b96a3', '#5d6875', '#2d3743',
  '#222b36', '#151b23', '#0d1117', '#090c10', '#05070a',
];

export const theme = createTheme({
  primaryColor: 'turf',
  primaryShade: 6,
  colors: { turf, dark },
  defaultRadius: 'md',
  fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
  headings: {
    fontFamily: 'Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
    fontWeight: '700',
  },
  components: {
    Card: { defaultProps: { withBorder: true, padding: 'lg', radius: 'md' } },
    Table: { defaultProps: { verticalSpacing: 'xs', horizontalSpacing: 'sm' } },
  },
});
