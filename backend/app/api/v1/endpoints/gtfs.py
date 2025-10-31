from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query

from backend.app.dependencies import get_loader, require_token
from backend.app.models.gtfs import (
    BootstrapPayload,
    GTFSResource,
    Route,
    RouteGeometry,
    ShapePoint,
    Stop,
    Trip,
)
from backend.app.services.gtfs_loader import GTFSDataLoader

router = APIRouter()


@router.get("/routes", response_model=list[Route])
def list_routes(
    limit: int = Query(50, ge=1, le=500),
    loader: GTFSDataLoader = Depends(get_loader),
    _: dict = Depends(require_token),
) -> list[Route]:
    df = loader.get_routes(limit=limit)
    return [Route(**record) for record in df.where(df.notnull(), None).to_dict(orient="records")]


@router.get("/stops", response_model=list[Stop])
def list_stops(
    limit: int = Query(50, ge=1, le=500),
    loader: GTFSDataLoader = Depends(get_loader),
    _: dict = Depends(require_token),
) -> list[Stop]:
    df = loader.get_stops(limit=limit)
    return [Stop(**record) for record in df.where(df.notnull(), None).to_dict(orient="records")]


@router.get("/trips", response_model=list[Trip])
def list_trips(
    route_id: str | None = Query(default=None, description="Filter by GTFS route_id"),
    limit: int = Query(50, ge=1, le=500),
    loader: GTFSDataLoader = Depends(get_loader),
    _: dict = Depends(require_token),
) -> list[Trip]:
    df = loader.get_trips()
    if route_id:
        df = df[df["route_id"] == route_id]
    df = df.head(limit)
    return [Trip(**record) for record in df.where(df.notnull(), None).to_dict(orient="records")]


@router.get("/shapes", response_model=list[ShapePoint])
def list_shapes(
    shape_id: str = Query(..., description="The GTFS shape_id to fetch."),
    limit: int = Query(250, ge=1, le=2000),
    loader: GTFSDataLoader = Depends(get_loader),
    _: dict = Depends(require_token),
) -> list[ShapePoint]:
    df = loader.get_shapes()
    df = df[df["shape_id"] == shape_id].sort_values("shape_pt_sequence").head(limit)
    return [ShapePoint(**record) for record in df.where(df.notnull(), None).to_dict(orient="records")]


@router.get("/resources", response_model=list[GTFSResource])
def list_resources(
    loader: GTFSDataLoader = Depends(get_loader),
    _: dict = Depends(require_token),
) -> list[GTFSResource]:
    tables = ["routes", "stops", "trips", "stop_times", "shapes"]
    resources: list[GTFSResource] = []
    for table in tables:
        path = loader.table_path(table)
        resources.append(
            GTFSResource(
                table=table,
                path=str(path),
                size_bytes=path.stat().st_size,
            )
        )
    return resources


@router.get("/bootstrap", response_model=BootstrapPayload)
def bootstrap(
    loader: GTFSDataLoader = Depends(get_loader),
    _: dict = Depends(require_token),
) -> BootstrapPayload:
    stops = [Stop(**row) for row in loader.get_stops_list()]
    routes_raw = loader.get_routes_dict()
    routes = {route_id: Route(**data) for route_id, data in routes_raw.items()}
    route_shapes = loader.get_route_shapes_map()
    stop_to_routes = loader.get_stop_route_map()
    metadata = {
        "stop_count": len(stops),
        "route_count": len(routes),
    }
    return BootstrapPayload(
        stops=stops,
        routes=routes,
        route_shapes=route_shapes,
        stop_to_routes=stop_to_routes,
        metadata=metadata,
    )


@router.get("/routes/{route_id}/geometry", response_model=RouteGeometry)
def route_geometry(
    route_id: str,
    loader: GTFSDataLoader = Depends(get_loader),
    _: dict = Depends(require_token),
) -> RouteGeometry:
    route_shapes = loader.get_route_shapes_map()
    shape_ids = route_shapes.get(route_id)
    if not shape_ids:
        raise HTTPException(status_code=404, detail=f"No shapes found for route {route_id}")

    shape_id = shape_ids[0]
    points = loader.get_shape_points(shape_id)
    if not points:
        raise HTTPException(status_code=404, detail=f"No geometry available for shape {shape_id}")

    return RouteGeometry(route_id=route_id, shape_id=shape_id, points=points)
