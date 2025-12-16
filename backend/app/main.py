from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, HTMLResponse
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
        """Landing page - redirect to login"""
        context = {"request": request}
        return templates.TemplateResponse("login.html", context)

    @app.get("/login", response_class=HTMLResponse)
    async def login_page(request: Request) -> HTMLResponse:
        """Login page"""
        context = {"request": request}
        return templates.TemplateResponse("login.html", context)

    @app.get("/signup", response_class=HTMLResponse)
    async def signup_page(request: Request) -> HTMLResponse:
        """Signup page"""
        context = {"request": request}
        return templates.TemplateResponse("signup.html", context)

    @app.get("/cards", response_class=HTMLResponse)
    async def cards(request: Request) -> HTMLResponse:
        """Card selection page"""
        context = {"request": request}
        return templates.TemplateResponse("cards.html", context)

    @app.get("/map", response_class=HTMLResponse)
    async def map_view(request: Request) -> HTMLResponse:
        """Assaults on Map - Main map functionality"""
        expires_delta = timedelta(minutes=settings.jwt_access_token_expire_minutes)
        token = create_access_token("cta-map-client", expires_delta)
        expires_at = datetime.now(timezone.utc) + expires_delta
        context = {
            "request": request,
            "initial_token": token,
            "token_expires_at": expires_at.isoformat(),
        }
        return templates.TemplateResponse("route.html", context)

    @app.get("/visualization", response_class=HTMLResponse)
    async def visualization(request: Request) -> HTMLResponse:
        """Assault Visualization - Interactive drag-and-drop builder"""
        context = {"request": request}
        return templates.TemplateResponse("visualization.html", context)

    @app.get("/viz-templates", response_class=HTMLResponse)
    async def viz_templates(request: Request) -> HTMLResponse:
        """Assault Visualization Templates - 20 pre-built charts"""
        context = {"request": request}
        return templates.TemplateResponse("viz_templates.html", context)

    @app.get("/view-chart", response_class=HTMLResponse)
    async def view_chart(request: Request) -> HTMLResponse:
        """Chart Viewer - Display individual templates or saved plots"""
        context = {"request": request}
        return templates.TemplateResponse("view_chart.html", context)

    @app.get("/my-plots", response_class=HTMLResponse)
    async def my_plots(request: Request) -> HTMLResponse:
        """My Saved Plots - View and manage saved visualizations"""
        context = {"request": request}
        return templates.TemplateResponse("my_plots.html", context)

    @app.get("/assaults.csv")
    async def assaults_csv() -> FileResponse:
        """Serve the cleaned CTA assaults CSV for front-end visualizations."""
        return FileResponse(
            path=settings.assault_data_file,
            media_type="text/csv",
            filename="Cleaned_CTA_Bus_Data.csv",
        )

    return app


app = create_app()
