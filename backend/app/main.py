from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from .api.router import api_router
from .core.config import settings

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
        return templates.TemplateResponse("route.html", {"request": request})

    return app


app = create_app()
