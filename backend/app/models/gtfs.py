from pydantic import BaseModel, ConfigDict


class Route(BaseModel):
    model_config = ConfigDict(extra="ignore")

    route_id: str
    route_short_name: str | None = None
    route_long_name: str | None = None
    route_desc: str | None = None
    route_type: int | None = None
    route_color: str | None = None
    route_text_color: str | None = None
    route_sort_order: int | None = None


class Stop(BaseModel):
    model_config = ConfigDict(extra="ignore")

    stop_id: str
    stop_code: str | None = None
    stop_name: str | None = None
    stop_desc: str | None = None
    stop_lat: float | None = None
    stop_lon: float | None = None
    wheelchair_boarding: str | None = None


class Trip(BaseModel):
    model_config = ConfigDict(extra="ignore")

    route_id: str
    service_id: str
    trip_id: str
    trip_headsign: str | None = None
    direction_id: int | None = None


class ShapePoint(BaseModel):
    model_config = ConfigDict(extra="ignore")

    shape_id: str
    shape_pt_lat: float
    shape_pt_lon: float
    shape_pt_sequence: int


class GTFSResource(BaseModel):
    model_config = ConfigDict(extra="ignore")

    table: str
    path: str
    size_bytes: int


class RouteGeometry(BaseModel):
    model_config = ConfigDict(extra="ignore")

    route_id: str
    shape_id: str
    points: list[list[float]]


class BootstrapMetadata(BaseModel):
    model_config = ConfigDict(extra="ignore")

    stop_count: int
    route_count: int


class BootstrapPayload(BaseModel):
    model_config = ConfigDict(extra="ignore")

    stops: list[Stop]
    routes: dict[str, Route]
    route_shapes: dict[str, list[str]]
    stop_to_routes: dict[str, list[str]]
    metadata: BootstrapMetadata
