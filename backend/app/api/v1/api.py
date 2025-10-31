from fastapi import APIRouter

from .endpoints import auth, gtfs

router = APIRouter()
router.include_router(gtfs.router, prefix="/gtfs", tags=["GTFS"])
router.include_router(auth.router, prefix="/auth", tags=["Auth"])
