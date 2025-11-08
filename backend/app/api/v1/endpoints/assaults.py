from fastapi import APIRouter, Depends

from backend.app.dependencies import require_token
from backend.app.models.assaults import AssaultIncident
from backend.app.services.assaults_loader import AssaultDataLoader, get_assault_loader

router = APIRouter()


@router.get("/", response_model=list[AssaultIncident])
def list_assaults(
    loader: AssaultDataLoader = Depends(get_assault_loader),
    _: dict = Depends(require_token),
) -> list[AssaultIncident]:
    """Return CTA assault incidents for mapping."""
    return loader.list_incidents()
