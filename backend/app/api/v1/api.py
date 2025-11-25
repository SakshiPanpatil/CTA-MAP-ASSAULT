from fastapi import APIRouter

from .endpoints import assaults, auth, gtfs, reports

router = APIRouter()
router.include_router(gtfs.router, prefix="/gtfs", tags=["GTFS"])
router.include_router(auth.router, prefix="/auth", tags=["Auth"])
router.include_router(assaults.router, prefix="/assaults", tags=["Assaults"])
router.include_router(reports.router, prefix="/reports", tags=["Reports"])
