from fastapi import APIRouter

from .endpoints import assaults, auth, forecasts, gtfs, plots, reports

router = APIRouter()
router.include_router(gtfs.router, prefix="/gtfs", tags=["GTFS"])
router.include_router(auth.router, prefix="/auth", tags=["Auth"])
router.include_router(assaults.router, prefix="/assaults", tags=["Assaults"])
router.include_router(reports.router, prefix="/reports", tags=["Reports"])
router.include_router(plots.router, prefix="/plots", tags=["Plots"])
router.include_router(forecasts.router, prefix="/forecasts", tags=["Forecasts"])
