from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from .api.router import api_router
from .core.config import settings
from .core.security import create_access_token

templates = Jinja2Templates(directory=str(settings.templates_directory))


def create_app() -> FastAPI:
    """Create and configure the FastAPI application instance."""
    app = FastAPI(
        title=settings.app_name,
        version=settings.version,
        docs_url=f"{settings.api_prefix}/docs",
        redoc_url=f"{settings.api_prefix}/redoc",
    )

    app.include_router(api_router, prefix=settings.api_prefix)

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
