"""Standalone script to build the stop-to-routes cache."""
import json
from collections import defaultdict
from pathlib import Path
import pandas as pd
import sys

# Fix encoding for Windows
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

# Configuration
DATA_DIR = Path(__file__).parent / "data"
CACHE_FILE = DATA_DIR / ".cache_stop_route_map.json"

print("=" * 60)
print("Building Stop-to-Routes Cache")
print("=" * 60)
print(f"Data directory: {DATA_DIR}")
print()

# Step 1: Load trips to get trip_id -> route_id mapping
print("[1/3] Loading trips.txt...")
trips_df = pd.read_csv(DATA_DIR / "trips.txt")
trip_to_route = trips_df.set_index("trip_id")["route_id"].to_dict()
print(f"  ✓ Loaded {len(trip_to_route):,} trips")
print()

# Step 2: Process stop_times.txt in chunks
print("[2/3] Processing stop_times.txt (5.8M rows)...")
print("  This will take ~10 minutes...")
mapping = defaultdict(set)

chunk_size = 100_000
chunk_count = 0

for chunk in pd.read_csv(DATA_DIR / "stop_times.txt", chunksize=chunk_size):
    chunk_count += 1

    # Extract only needed columns and drop nulls
    minimal = chunk.loc[:, ["trip_id", "stop_id"]].dropna()

    # Map trip_id to route_id
    minimal["route_id"] = minimal["trip_id"].map(trip_to_route)
    minimal = minimal.dropna(subset=["route_id"])

    # Group by stop_id and collect unique route_ids
    grouped = minimal.groupby("stop_id")["route_id"].unique()
    for stop_id, routes in grouped.items():
        mapping[str(stop_id)].update(map(str, routes))

    if chunk_count % 10 == 0:
        print(f"  ... processed {chunk_count * chunk_size:,} rows")

print(f"  ✓ Processed all chunks")
print(f"  ✓ Found {len(mapping):,} stops")
print()

# Step 3: Save to cache file
print("[3/3] Saving cache...")
result = {stop_id: sorted(routes) for stop_id, routes in mapping.items()}

with open(CACHE_FILE, 'w') as f:
    json.dump(result, f)

cache_size_mb = CACHE_FILE.stat().st_size / (1024**2)
print(f"  ✓ Cache saved: {cache_size_mb:.2f} MB")
print()

print("=" * 60)
print("✓ Cache build complete!")
print("=" * 60)
print()
print("Next steps:")
print("1. Restart your uvicorn server (Ctrl+C and rerun)")
print("2. Refresh your browser")
print("3. Routes should now load instantly!")
