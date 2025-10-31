from __future__ import annotations

from collections import defaultdict
from functools import lru_cache
from pathlib import Path
from typing import Iterable, Optional

import pandas as pd


class GTFSDataLoader:
    """Utility for loading GTFS tables with optional in-memory caching."""

    def __init__(self, data_dir: Path, cache_tables: Optional[Iterable[str]] = None) -> None:
        self.data_dir = Path(data_dir)
        default_cache = {"routes", "stops", "trips", "shapes"}
        self.cache_tables = set(cache_tables or []) | default_cache
        self._cache: dict[str, pd.DataFrame] = {}
        self._computed: dict[str, object] = {}

    def table_path(self, table_name: str) -> Path:
        path = self.data_dir / f"{table_name}.txt"
        if not path.exists():
            raise FileNotFoundError(f"GTFS table {table_name!r} not found at {path}")
        return path

    def load_table(
        self,
        table_name: str,
        *,
        limit: Optional[int] = None,
        chunksize: Optional[int] = None,
        dtype: Optional[dict[str, str]] = None,
        usecols: Optional[list[str]] = None,
    ) -> pd.DataFrame | Iterable[pd.DataFrame]:
        """Load a GTFS table, optionally chunking or limiting rows for large files."""
        if chunksize:
            return pd.read_csv(
                self.table_path(table_name),
                sep=",",
                dtype=dtype,
                usecols=usecols,
                chunksize=chunksize,
            )

        if table_name in self._cache:
            df = self._cache[table_name]
        else:
            df = pd.read_csv(
                self.table_path(table_name),
                sep=",",
                dtype=dtype,
                usecols=usecols,
            )
            if table_name in self.cache_tables:
                self._cache[table_name] = df

        if limit is not None:
            return df.head(limit)
        return df

    def get_routes(self, *, limit: Optional[int] = None) -> pd.DataFrame:
        return self.load_table("routes", limit=limit)

    def get_stops(self, *, limit: Optional[int] = None) -> pd.DataFrame:
        return self.load_table("stops", limit=limit)

    def get_trips(self, *, limit: Optional[int] = None) -> pd.DataFrame:
        return self.load_table("trips", limit=limit)

    def get_stop_times(
        self,
        *,
        limit: Optional[int] = None,
        chunksize: Optional[int] = 50000,
    ) -> pd.DataFrame | Iterable[pd.DataFrame]:
        """Default to chunked loading for the very large stop_times table."""
        if limit is not None and chunksize:
            # If both limit and chunksize supplied, load normally then trim.
            chunksize = None
        return self.load_table("stop_times", limit=limit, chunksize=chunksize)

    def get_shapes(self, *, limit: Optional[int] = None) -> pd.DataFrame:
        return self.load_table("shapes", limit=limit)

    def _get_df(self, table_name: str) -> pd.DataFrame:
        """Return an uncropped DataFrame for the table."""
        df = self.load_table(table_name)
        if isinstance(df, pd.DataFrame):
            return df
        # If load_table returned an iterator (because chunksize supplied), reload without chunks.
        return self.load_table(table_name, chunksize=None)  # type: ignore[arg-type]

    def _json_records(self, df: pd.DataFrame) -> list[dict]:
        """Convert DataFrame into JSON-serialisable records with nulls preserved."""
        safe_df = df.where(pd.notnull(df), None)
        return safe_df.to_dict(orient="records")

    def get_routes_dict(self) -> dict[str, dict]:
        if "routes_dict" not in self._computed:
            routes_df = self._get_df("routes")
            records = self._json_records(routes_df)
            for row in records:
                if "route_id" in row and row["route_id"] is not None:
                    row["route_id"] = str(row["route_id"])
                if "route_short_name" in row and row["route_short_name"] is not None:
                    row["route_short_name"] = str(row["route_short_name"])
                if "route_long_name" in row and row["route_long_name"] is not None:
                    row["route_long_name"] = str(row["route_long_name"])
                if "route_desc" in row and row["route_desc"] is not None:
                    row["route_desc"] = str(row["route_desc"])
            self._computed["routes_dict"] = {row["route_id"]: row for row in records}
        return self._computed["routes_dict"]  # type: ignore[return-value]

    def get_stops_list(self) -> list[dict]:
        if "stops_list" not in self._computed:
            stops_df = self._get_df("stops")
            records = self._json_records(stops_df)
            for row in records:
                if "stop_id" in row and row["stop_id"] is not None:
                    row["stop_id"] = str(row["stop_id"])
                if "stop_code" in row and row["stop_code"] not in (None, ""):
                    row["stop_code"] = str(row["stop_code"])
                if "stop_name" in row and row["stop_name"] is not None:
                    row["stop_name"] = str(row["stop_name"])
                if "stop_desc" in row and row["stop_desc"] is not None:
                    row["stop_desc"] = str(row["stop_desc"])
                if "wheelchair_boarding" in row and row["wheelchair_boarding"] not in (None, ""):
                    row["wheelchair_boarding"] = str(row["wheelchair_boarding"])
            self._computed["stops_list"] = records
        return self._computed["stops_list"]  # type: ignore[return-value]

    def get_route_shapes_map(self) -> dict[str, list[str]]:
        if "route_shapes_map" not in self._computed:
            trips_df = self._get_df("trips")
            if "shape_id" not in trips_df.columns:
                self._computed["route_shapes_map"] = {}
            else:
                shapes_map = (
                    trips_df.dropna(subset=["shape_id"])
                    .groupby("route_id")["shape_id"]
                    .apply(lambda values: list(dict.fromkeys(map(str, values))))
                    .to_dict()
                )
                self._computed["route_shapes_map"] = shapes_map
        return self._computed["route_shapes_map"]  # type: ignore[return-value]

    def get_shape_points(self, shape_id: str) -> list[list[float]]:
        shapes_key = f"shape_points::{shape_id}"
        if shapes_key in self._computed:
            return self._computed[shapes_key]  # type: ignore[return-value]

        shapes_df = self._get_df("shapes")
        filtered = (
            shapes_df[shapes_df["shape_id"] == shape_id]
            .sort_values("shape_pt_sequence")
            .loc[:, ["shape_pt_lat", "shape_pt_lon"]]
        )
        points = [
            [float(row.shape_pt_lat), float(row.shape_pt_lon)]
            for row in filtered.itertuples(index=False)
        ]
        self._computed[shapes_key] = points
        return points

    def get_stop_route_map(self) -> dict[str, list[str]]:
        if "stop_route_map" in self._computed:
            return self._computed["stop_route_map"]  # type: ignore[return-value]

        trips_df = self._get_df("trips")
        trip_to_route = trips_df.set_index("trip_id")["route_id"].to_dict()
        mapping: defaultdict[str, set[str]] = defaultdict(set)

        stop_times_data = self.get_stop_times(chunksize=100_000)
        if isinstance(stop_times_data, pd.DataFrame):
            iterable = [stop_times_data]
        else:
            iterable = stop_times_data

        for chunk in iterable:
            minimal = chunk.loc[:, ["trip_id", "stop_id"]].dropna()
            minimal["route_id"] = minimal["trip_id"].map(trip_to_route)
            minimal = minimal.dropna(subset=["route_id"])
            grouped = minimal.groupby("stop_id")["route_id"].unique()
            for stop_id, routes in grouped.items():
                mapping[str(stop_id)].update(map(str, routes))

        result = {stop_id: sorted(routes) for stop_id, routes in mapping.items()}
        self._computed["stop_route_map"] = result
        return result


@lru_cache
def get_default_loader() -> GTFSDataLoader:
    """Return a GTFS loader configured for the default data directory."""
    from backend.app.core.config import settings

    cache_candidates = {"routes", "stops"}
    return GTFSDataLoader(settings.data_directory, cache_tables=cache_candidates)
