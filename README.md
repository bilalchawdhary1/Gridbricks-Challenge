# Wind Forecast Portal

Day-ahead UK wind forecast and accuracy dashboard for power procurement,
built on Elexon BMRS data (FUELHH actuals, WINDFOR forecasts), January 2026.

**Live app:** https://frontend-chi-neon-18.vercel.app
**API:** https://backend-ten-eta-23.vercel.app/docs
**Video walkthrough:** [unlisted YouTube link]

## What it does

1. **Day-ahead forecast:** for a delivery day D, shows the latest wind
   forecast published before the decision cutoff (D-1, 09:00 UK time).
2. **Forecast accuracy:** compares those forecasts with actual generation
   for a chosen date range. Metrics: MAE, RMSE, bias, WAPE, coverage,
   plus error by hour of day.

## Key design decisions

- **Cutoff:** each delivery day is scored using the latest forecast
  published by 09:00 UK time on D-1 (configurable via `DECISION_HOUR` /
  `DECISION_MINUTE`). This is an assumption about day-ahead gate closure.
- **Hourly comparison:** half-hourly actuals are averaged to hourly and
  only complete hours are used, to match the hourly forecasts.
- **No look-ahead:** forecasts published after the cutoff are never used.
- **Data source:** forecast snapshots come from the Elexon WINDFOR
  forecast-history endpoint. January 2026 is pre-downloaded into
  `backend/data/` (`backend/scripts/build_snapshot.py`) so the deployed
  app is fast and does not depend on Elexon being available. If a file is
  missing, the backend falls back to the live API.

## Repository layout

```
backend/
  app/main.py              FastAPI app, CORS
  app/api/data.py          /api/data/forecast and /api/data/accuracy
  app/services/cutoff.py   D-1 decision cutoff
  app/services/elexon.py   Elexon client + snapshot loader
  app/services/matching.py normalisation, hourly aggregation, matching
  app/services/accuracy_metrics.py
  data/                    January 2026 snapshot (JSON)
  scripts/build_snapshot.py  regenerates data/ from Elexon
  tests/                   pytest suite
frontend/                  React + Vite + TypeScript + Recharts
docker-compose.yml
```

## Run with Docker

```
docker compose up --build
```

Frontend: http://localhost:3000, API: http://localhost:8000/docs

## Run locally

```
cd backend && pip install -r requirements.txt
uvicorn app.main:app --reload

cd frontend && npm install
echo VITE_API_BASE_URL=http://localhost:8000 > .env
npm run dev
```

Tests: `cd backend && pytest`

## Configuration

| Variable                           | Where                 | Purpose                                |
| ---------------------------------- | --------------------- | -------------------------------------- |
| `VITE_API_BASE_URL`                | frontend (build time) | Backend URL, no trailing slash         |
| `CORS_ORIGINS`                     | backend               | Extra allowed origins, comma-separated |
| `DECISION_HOUR`, `DECISION_MINUTE` | backend               | Day-ahead cutoff (default 09:00)       |

## Deployment

Frontend and backend are separate Vercel projects (root directories
`frontend` and `backend`).

## AI usage

I used AI tools (Claude) to assist with design discussions, code and
debugging. I reviewed, tested and understand the code I submitted.

## Limitations

- Scope is January 2026 and national-level wind only.
- The 09:00 cutoff is an assumption.
