from __future__ import annotations

import csv
from functools import lru_cache
from pathlib import Path
from threading import Lock

from backend.app.core.config import settings
from backend.app.models.assaults import AssaultIncident


class AssaultDataLoader:
    """Load and cache CTA assault data for quick API access."""

    def __init__(self, csv_path: Path) -> None:
        self.csv_path = Path(csv_path)
        self._lock = Lock()
        self._cache: list[AssaultIncident] | None = None

    def list_incidents(self) -> list[AssaultIncident]:
        """Return cached assault incidents, loading from disk if necessary."""
        if self._cache is None:
            with self._lock:
                if self._cache is None:
                    self._cache = self._load_from_disk()
        return self._cache

    # Internal helpers -------------------------------------------------
    def _load_from_disk(self) -> list[AssaultIncident]:
        incidents: list[AssaultIncident] = []
        if not self.csv_path.exists():
            return incidents

        with self.csv_path.open(newline="", encoding="utf-8") as handle:
            reader = csv.DictReader(handle)
            for row in reader:
                lat = self._as_float(row.get("Latitude"))
                lon = self._as_float(row.get("Longitude"))
                if lat is None or lon is None:
                    continue

                total_injuries = self._as_int(row.get("Total Injuries")) or 0
                operator_injuries = (
                    self._as_int(row.get("Transit Vehicle Operator Injuries")) or 0
                )
                rider_injuries = (
                    self._as_int(row.get("Transit Vehicle Rider Injuries")) or 0
                )

                incident = AssaultIncident(
                    ntd_id=self._as_int(row.get("NTD ID")),
                    incident_number=self._as_int(row.get("Incident Number")),
                    event_date=self._clean(row.get("Event Date")),
                    event_time=self._clean(row.get("Event Time")),
                    event_type=self._clean(row.get("Event Type")),
                    event_type_group=self._clean(row.get("Event Type Group")),
                    location_type=self._clean(row.get("Location Type")),
                    approximate_address=self._clean(row.get("Approximate Address")),
                    latitude=lat,
                    longitude=lon,
                    total_injuries=total_injuries,
                    total_fatalities=self._as_int(row.get("Total Fatalities")) or 0,
                    transit_vehicle_operator_injuries=operator_injuries,
                    transit_vehicle_rider_injuries=rider_injuries,
                    description=self._clean(row.get("Event Description")),
                    severity_score=self._severity_score(
                        total_injuries=total_injuries,
                        rider_injuries=rider_injuries,
                        operator_injuries=operator_injuries,
                        category=self._clean(row.get("Event Type Group")),
                        worker_flag=self._clean(row.get("Transit Worker Assault Flag")),
                    ),
                )
                incidents.append(incident)

        return incidents

    @staticmethod
    def _clean(value: str | None) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    @staticmethod
    def _as_float(value: str | None) -> float | None:
        try:
            if value is None or value == "":
                return None
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _as_int(value: str | None) -> int | None:
        try:
            if value is None or value == "":
                return None
            return int(float(value))
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _severity_score(
        *,
        total_injuries: int,
        rider_injuries: int,
        operator_injuries: int,
        category: str | None,
        worker_flag: str | None,
    ) -> int:
        """Create a coarse severity bucket (1-5) for styling in the UI."""
        score = 1
        injury_load = total_injuries + rider_injuries + operator_injuries
        if injury_load:
            score += min(3, injury_load)

        if category and category.lower() == "assault":
            score += 1

        if worker_flag and worker_flag.lower() == "true":
            score += 1

        return max(1, min(5, score))


@lru_cache
def get_assault_loader() -> AssaultDataLoader:
    return AssaultDataLoader(settings.assault_data_file)
