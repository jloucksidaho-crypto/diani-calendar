"""
Serves tide data from a locally bundled tides_data.json file.
No API calls are made during normal operation.
Run generate_tides.py once a year to refresh the data file.
"""

import json
import time
from pathlib import Path

_DATA_FILE = Path(__file__).parent / "tides_data.json"

# Module-level cache — loaded once per server session
_cache: list = []


def get_tides() -> list:
    global _cache

    if _cache:
        return _cache

    if not _DATA_FILE.exists():
        raise RuntimeError(
            "tides_data.json not found. "
            "Run generate_tides.py to create it, then commit the file to GitHub."
        )

    data = json.loads(_DATA_FILE.read_text())
    now = time.time()

    # Return only upcoming events (within the last hour and forward)
    extremes = [e for e in data.get("extremes", []) if e.get("dt", 0) >= now - 3600]

    # Log a warning when fewer than 30 days of data remain
    if extremes:
        days_left = (extremes[-1]["dt"] - now) / 86400
        if days_left < 30:
            print(
                f"NOTICE: Tide data has {days_left:.0f} days remaining. "
                "Run generate_tides.py soon and commit the updated tides_data.json."
            )

    _cache = extremes
    return _cache
