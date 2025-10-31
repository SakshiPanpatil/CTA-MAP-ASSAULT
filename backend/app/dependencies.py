from collections.abc import Iterator

from .services.gtfs_loader import GTFSDataLoader, get_default_loader


def get_loader() -> Iterator[GTFSDataLoader]:
    """FastAPI dependency that yields a reusable GTFS loader instance."""
    loader = get_default_loader()
    yield loader
