# Prem Scout frontend

React + Vite + Mantine dashboard for the Prem Scout scouting platform. See the [root README](../README.md) for what this project does, the API it talks to, and how to run the whole stack.

## Local dev

```bash
npm install
npm run dev
```

Runs at `http://localhost:5173` and reads the pre-exported data in `public/data/` (regenerate with `backend/scripts/export_static_api.py`); no backend is needed.

## Structure

- `src/pages/` - Dashboard, Rankings, PlayerProfile
- `src/components/` - shared UI pieces (filters, stat cards, explanation breakdown)
- `src/services/api.js` - all backend calls
- `src/theme.js` - custom Mantine theme (pitch green / rust, not the default indigo)

## Linting

```bash
npm run lint
```

Uses [oxlint](https://oxc.rs) with React-specific rules; config is in `.oxlintrc.json`.
