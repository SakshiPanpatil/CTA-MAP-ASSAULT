# CTA-MAP-ASSAULT

Interactive CTA route visualisation backed by a modular FastAPI service.

## Project layout

- `backend/app/templates/route.html` - Jinja template rendered by FastAPI, powered by the GTFS APIs.
- `data/` - raw GTFS exports (routes, stops, trips, shapes, stop_times).
- `backend/app/` - FastAPI application, routers, models, and GTFS data services.

## Run the app (FastAPI)

1. Copy `.env.example` to `.env` and provide strong values for `JWT_SECRET_KEY` and `ACCESS_PASSPHRASE`.
2. Create a virtual environment and install dependencies: `python -m venv .venv && .venv\Scripts\activate && pip install -r requirements.txt`.
3. Run the development server: `uvicorn backend.app.main:app --reload`.
4. Visit `http://127.0.0.1:8000/` for the interactive map (data is supplied by FastAPI). The server issues a short-lived JWT automatically using the passphrase you configured.
5. Explore the auto-generated docs at `http://127.0.0.1:8000/api/docs`.

## Authentication

- Token issuance lives at `POST /api/v1/auth/token` and expects JSON like `{"secret_key": "<your ACCESS_PASSPHRASE>"}`. The FastAPI root route pre-issues a token on render, embedding it in the page. Expiry handling remains automatic.
- All GTFS endpoints (bootstrap, geometry, tables, metadata) require the `Authorization: Bearer <token>` header. The frontend template stores the token in `sessionStorage`, reuses the embedded token, and reprompts only if it expires with no server refresh.
- Override the secret, signing key, or expiration via environment variables (`ACCESS_PASSPHRASE`, `JWT_SECRET_KEY`, etc.) without changing code.

The scaffold includes:

- Centralised settings (`backend/app/core/config.py`) with automatic data directory discovery.
- A GTFS loader service (`backend/app/services/gtfs_loader.py`) for cached table access plus precomputed stop ↔ route and route ↔ shape lookups.
- Versioned API routers (`backend/app/api/v1/`) exposing bootstrap data, route geometry, classic GTFS tables, and resource metadata.

Use these modules as the integration points for additional FastAPI endpoints or alternative frontends.
