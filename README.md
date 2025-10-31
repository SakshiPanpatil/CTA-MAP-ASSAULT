# CTA-MAP-ASSAULT

Interactive CTA route visualisation backed by a modular FastAPI service.

## Project layout

- `backend/app/templates/route.html` - Jinja template rendered by FastAPI, powered by the GTFS APIs.
- `data/` - raw GTFS exports (routes, stops, trips, shapes, stop_times).
- `backend/app/` - FastAPI application, routers, models, and GTFS data services.

## Run the app (FastAPI)

1. Create a virtual environment and install dependencies: `python -m venv .venv && .venv\Scripts\activate && pip install -r requirements.txt`.
2. Run the development server: `uvicorn backend.app.main:app --reload`.
3. Visit `http://127.0.0.1:8000/` for the interactive map (data is supplied by FastAPI).
4. Explore the auto-generated docs at `http://127.0.0.1:8000/api/docs`.

The scaffold includes:

- Centralised settings (`backend/app/core/config.py`) with automatic data directory discovery.
- A GTFS loader service (`backend/app/services/gtfs_loader.py`) for cached table access plus precomputed stop ↔ route and route ↔ shape lookups.
- Versioned API routers (`backend/app/api/v1/`) exposing bootstrap data, route geometry, classic GTFS tables, and resource metadata.

Use these modules as the integration points for additional FastAPI endpoints or alternative frontends.
