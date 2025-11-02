from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .api.router import api_router
from .core.config import settings
from .core.security import create_access_token
from .services.bootstrap_cache import get_bootstrap_cache

templates = Jinja2Templates(directory=str(settings.templates_directory))


def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance."""
    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
        docs_url=f"{settings.api_prefix}/docs",
        redoc_url=f"{settings.api_prefix}/redoc",
    )

    app.mount("/static", StaticFiles(directory=str(settings.static_directory)), name="static")
    app.include_router(api_router, prefix=settings.api_prefix)
    get_bootstrap_cache()

    @app.get("/", response_class=HTMLResponse)
    async def root(request: Request) -> HTMLResponse:
        expires_delta = timedelta(minutes=settings.jwt_access_token_expire_minutes)
        token = create_access_token("cta-map-client", expires_delta)
        expires_at = datetime.now(timezone.utc) + expires_delta
        context = {
            "request": request,
            "initial_token": token,
            "token_expires_at": expires_at.isoformat(),
        }
        return templates.TemplateResponse("route.html", context)

    return app


app = create_app()
