from pydantic import BaseModel, ConfigDict


class AssaultIncident(BaseModel):
    model_config = ConfigDict(extra="ignore")

    ntd_id: int | None = None
    incident_number: int | None = None
    event_date: str | None = None
    event_time: str | None = None
    event_type: str | None = None
    event_type_group: str | None = None
    location_type: str | None = None
    approximate_address: str | None = None
    latitude: float
    longitude: float
    total_injuries: int = 0
    total_fatalities: int = 0
    transit_vehicle_operator_injuries: int = 0
    transit_vehicle_rider_injuries: int = 0
    description: str | None = None
    severity_score: int = 1
