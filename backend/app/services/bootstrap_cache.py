from __future__ import annotations

from threading import Lock, Thread
from typing import Dict, Iterable, List

from ..models.bootstrap import BootstrapProgress, BootstrapResponse
from ..models.gtfs import BootstrapMetadata, BootstrapPayload, Route, Stop
from .gtfs_loader import GTFSDataLoader, get_default_loader


class BootstrapCache:
    PROGRESS_ORDER: List[str] = [
        "step-stops",
        "step-routes",
        "step-trips",
        "step-shapes",
        "step-stoptimes",
        "step-processing",
    ]

    def __init__(self, loader: GTFSDataLoader) -> None:
        self.loader = loader
        self._lock = Lock()
        self._status: str = "warming"
        self._progress: Dict[str, str] = {step: "pending" for step in self.PROGRESS_ORDER}
        self._error: str | None = None

        self._stops: List[Stop] = []
        self._routes: Dict[str, Route] = {}
        self._route_shapes: Dict[str, List[str]] = {}
        self._stop_to_routes: Dict[str, List[str]] = {}

        self._partial_payload: BootstrapPayload | None = None
        self._final_payload: BootstrapPayload | None = None

        self._builder_thread = Thread(target=self._build_payload, daemon=True)
        self._builder_thread.start()

    # Progress helpers -------------------------------------------------
    def _set_progress(self, step: str, status: str) -> None:
        with self._lock:
            self._progress[step] = status

    def _set_status(self, status: str, message: str | None = None) -> None:
        with self._lock:
            self._status = status
            self._error = message

    # Payload helpers --------------------------------------------------
    def _refresh_partial_payload(self) -> None:
        metadata = BootstrapMetadata(
            stop_count=len(self._stops),
            route_count=len(self._routes),
        )
        self._partial_payload = BootstrapPayload(
            stops=self._stops,
            routes=self._routes,
            route_shapes=self._route_shapes,
            stop_to_routes=self._stop_to_routes,
            metadata=metadata,
        )

    def _build_payload(self) -> None:
        try:
            # Stops
            self._set_progress("step-stops", "active")
            stops_raw = self.loader.get_stops_list()
            stops = [Stop(**row) for row in stops_raw]
            with self._lock:
                self._stops = stops
                self._refresh_partial_payload()
            self._set_progress("step-stops", "complete")

            # Routes
            self._set_progress("step-routes", "active")
            routes_raw = self.loader.get_routes_dict()
            routes = {route_id: Route(**data) for route_id, data in routes_raw.items()}
            with self._lock:
                self._routes = routes
                self._refresh_partial_payload()
            self._set_progress("step-routes", "complete")

            # Route shapes (based on trips)
            self._set_progress("step-trips", "active")
            route_shapes = self.loader.get_route_shapes_map()
            with self._lock:
                self._route_shapes = route_shapes
                self._refresh_partial_payload()
            self._set_progress("step-trips", "complete")

            # Shapes processed
            self._set_progress("step-shapes", "active")
            self._set_progress("step-shapes", "complete")

            # Stop-time relationships
            self._set_progress("step-stoptimes", "active")
            stop_to_routes = self.loader.get_stop_route_map()
            with self._lock:
                # Ensure values are sorted lists for stable serialisation
                formatted = {stop_id: list(routes) for stop_id, routes in stop_to_routes.items()}
                self._stop_to_routes = formatted
                self._refresh_partial_payload()
            self._set_progress("step-stoptimes", "complete")

            # Final processing
            self._set_progress("step-processing", "active")
            with self._lock:
                self._final_payload = self._partial_payload
            self._set_progress("step-processing", "complete")
            self._set_status("ready")
        except Exception as exc:  # noqa: BLE001
            self._set_progress("step-processing", "error")
            self._set_status("error", str(exc))

    # Public API -------------------------------------------------------
    def get_response(self, include_payload: bool = True) -> BootstrapResponse:
        with self._lock:
            status = self._status
            message = self._error
            progress_states = list(self._progress.items())
            payload = None
            if include_payload:
                if status == "ready" and self._final_payload is not None:
                    payload = self._final_payload
                elif self._partial_payload is not None:
                    payload = self._partial_payload

        progress_models = [
            BootstrapProgress(step=step, status=state) for step, state in progress_states
        ]

        return BootstrapResponse(
            status=status,
            progress=progress_models,
            payload=payload,
            message=message,
        )


_bootstrap_cache: BootstrapCache | None = None


def get_bootstrap_cache() -> BootstrapCache:
    global _bootstrap_cache  # noqa: PLW0603
    if _bootstrap_cache is None:
        loader = get_default_loader()
        _bootstrap_cache = BootstrapCache(loader)
    return _bootstrap_cache
