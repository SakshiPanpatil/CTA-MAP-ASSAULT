
# CTA-MAP-ASSAULT

Interactive CTA route visualisation backed by a modular FastAPI service.

## Project layout

- `backend/app/templates/route.html` - Jinja template rendered by FastAPI, powering the Leaflet frontend.
- `backend/app/static/` - static assets (CTA branding, icons) served by FastAPI.
- `backend/app/` - FastAPI application, routers, models, and GTFS data services.
- `data/` - raw GTFS exports (routes, stops, trips, shapes, stop_times).

## Run the app (FastAPI)

1. Copy `.env.example` to `.env` and provide strong values for `JWT_SECRET_KEY` and `ACCESS_PASSPHRASE`.
2. Create a virtual environment and install dependencies: `python -m venv .venv && .venv\Scripts\activate && pip install -r requirements.txt`.
3. Run the development server: `uvicorn backend.app.main:app --reload`.
4. Visit `http://127.0.0.1:8000/` for the interactive map. The server issues a short-lived JWT automatically using the passphrase you configured.
5. Explore the auto-generated docs at `http://127.0.0.1:8000/api/docs`.

The backend warms the heavy GTFS relationships (route shapes, stop-to-route mapping) in a background thread. The map renders as soon as stops and routes are available, and route badges appear once the warm-up finishes.

## Authentication

- Token issuance lives at `POST /api/v1/auth/token` and expects JSON like `{"secret_key": "<your ACCESS_PASSPHRASE>"}`. The FastAPI root route pre-issues a token on render, embedding it in the page.
- All GTFS endpoints (bootstrap, geometry, tables, metadata) require the `Authorization: Bearer <token>` header. The frontend keeps the token in `sessionStorage`, reusing it until expiry.
- Override the secret, signing key, or expiration via environment variables (`ACCESS_PASSPHRASE`, `JWT_SECRET_KEY`, etc.) without changing code.

## What's inside

- Centralised settings (`backend/app/core/config.py`) with automatic data, template, and static directory discovery.
- A GTFS loader service (`backend/app/services/gtfs_loader.py`) with shared caching, guarded concurrency, and stop-to-route plus route-to-shape lookups.
- Versioned API routers (`backend/app/api/v1/`) exposing bootstrap data, route geometry, classic GTFS tables, and resource metadata.

Use these modules as the integration points for additional FastAPI endpoints or alternative frontends.

