from __future__ import annotations

from collections import defaultdict
from functools import lru_cache
from pathlib import Path
from typing import Iterable, Optional
import json

import pandas as pd
from threading import Lock


class GTFSDataLoader:
    """Utility for loading GTFS tables with optional in-memory caching."""

    def __init__(self, data_dir: Path, cache_tables: Optional[Iterable[str]] = None) -> None:
        self.data_dir = Path(data_dir)
        default_cache = {"routes", "stops", "trips", "shapes"}
        self.cache_tables = set(cache_tables or []) | default_cache
        self._cache: dict[str, pd.DataFrame] = {}
        self._computed: dict[str, object] = {}
        self._lock = Lock()

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

        with self._lock:
            cached_df = self._cache.get(table_name)
        if cached_df is not None:
            df = self._normalize_df(table_name, cached_df)
        else:
            df = pd.read_csv(
                self.table_path(table_name),
                sep=",",
                dtype=dtype,
                usecols=usecols,
            )
            df = self._normalize_df(table_name, df)
            if table_name in self.cache_tables:
                with self._lock:
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

    @staticmethod
    def _stringify_series(series: pd.Series) -> pd.Series:
        def convert(value):
            if value is None or (isinstance(value, float) and pd.isna(value)):
                return None
            if isinstance(value, (int, float)):
                if isinstance(value, float) and not value.is_integer():
                    return str(value).rstrip('0').rstrip('.')
                return str(int(value))
            value_str = str(value).strip()
            if value_str.endswith('.0') and value_str.replace('.', '', 1).isdigit():
                return value_str[:-2]
            return value_str

        return series.apply(convert)
    def _normalize_df(self, table_name: str, df: pd.DataFrame) -> pd.DataFrame:
        if table_name == "routes":
            for column in ("route_id", "route_short_name", "route_long_name", "route_desc", "route_text_color", "route_color"):
                if column in df.columns:
                    df[column] = self._stringify_series(df[column])
        elif table_name == "stops":
            for column in ("stop_id", "stop_code", "stop_name", "stop_desc", "wheelchair_boarding"):
                if column in df.columns:
                    df[column] = self._stringify_series(df[column])
        elif table_name == "trips":
            for column in ("trip_id", "route_id", "shape_id"):
                if column in df.columns:
                    df[column] = self._stringify_series(df[column])
        elif table_name == "shapes":
            if "shape_id" in df.columns:
                df["shape_id"] = self._stringify_series(df["shape_id"])
        elif table_name == "stop_times":
            for column in ("trip_id", "stop_id"):
                if column in df.columns:
                    df[column] = self._stringify_series(df[column])
        return df

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
            with self._lock:
                if "routes_dict" not in self._computed:
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
            with self._lock:
                if "stops_list" not in self._computed:
                    self._computed["stops_list"] = records
        return self._computed["stops_list"]  # type: ignore[return-value]

    def get_route_shapes_map(self) -> dict[str, list[str]]:
        if "route_shapes_map" not in self._computed:
            trips_df = self._get_df("trips")
            if "shape_id" not in trips_df.columns:
                shapes_map: dict[str, list[str]] = {}
            else:
                grouped = (
                    trips_df.dropna(subset=["shape_id"])
                    .groupby("route_id")["shape_id"]
                    .apply(lambda values: list(dict.fromkeys(map(str, values))))
                )
                shapes_map = {str(route_id): shapes for route_id, shapes in grouped.items()}
            with self._lock:
                if "route_shapes_map" not in self._computed:
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
        with self._lock:
            self._computed[shapes_key] = points
        return points

    def get_stop_route_map(self) -> dict[str, list[str]]:
        if "stop_route_map" in self._computed:
            return self._computed["stop_route_map"]  # type: ignore[return-value]

        # Try to load from cache file first
        cache_file = self.data_dir / ".cache_stop_route_map.json"
        stop_times_path = self.table_path("stop_times")

        # Check if cache exists, is newer than stop_times.txt, and has data
        if cache_file.exists():
            cache_stat = cache_file.stat()
            cache_mtime = cache_stat.st_mtime
            cache_size = cache_stat.st_size
            stop_times_mtime = stop_times_path.stat().st_mtime

            # Cache must be newer AND have actual data (more than just "{}")
            if cache_mtime > stop_times_mtime and cache_size > 10:
                # Cache is valid, load it
                try:
                    with open(cache_file, 'r') as f:
                        result = json.load(f)
                    # Validate that result is not empty
                    if result and len(result) > 0:
                        with self._lock:
                            if "stop_route_map" not in self._computed:
                                self._computed["stop_route_map"] = result
                        return result
                    print("Warning: Cached stop_route_map is empty, rebuilding...")
                except Exception as e:
                    # If cache loading fails, rebuild it
                    print(f"Warning: Failed to load stop_route_map cache: {e}")

        # Cache doesn't exist or is stale, build it
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

        # Save to cache file
        try:
            with open(cache_file, 'w') as f:
                json.dump(result, f)
        except Exception as e:
            print(f"Warning: Failed to save stop_route_map cache: {e}")

        with self._lock:
            if "stop_route_map" not in self._computed:
                self._computed["stop_route_map"] = result
        return self._computed["stop_route_map"]  # type: ignore[return-value]


@lru_cache
def get_default_loader() -> GTFSDataLoader:
    """Return a GTFS loader configured for the default data directory."""
    from backend.app.core.config import settings

    cache_candidates = {"routes", "stops"}
    return GTFSDataLoader(settings.data_directory, cache_tables=cache_candidates)






