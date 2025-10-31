from fastapi import APIRouter

from .endpoints import gtfs

router = APIRouter()
router.include_router(gtfs.router, prefix="/gtfs", tags=["GTFS"])
