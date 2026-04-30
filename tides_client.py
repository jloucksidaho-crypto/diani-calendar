import json
import os
import time
from pathlib import Path

import requests

_API_URL = "https://www.worldtides.info/api/v3"
_DIANI_LAT = -4.3167
_DIANI_LON = 39.5667
_CACHE_FILE = Path("/tmp/tides_cache.json")
_CACHE_TTL = 21600  # re-fetch every 6 hours


def get_tides() -> list:
    if _CACHE_FILE.exists():
        try:
            cached = json.loads(_CACHE_FILE.read_text())
            if time.time() - cached.get("fetched_at", 0) < _CACHE_TTL:
                return cached["extremes"]
        except (json.JSONDecodeError, KeyError):
            pass

    resp = requests.get(
        _API_URL,
        params={
            "extremes": "",
            "lat": _DIANI_LAT,
            "lon": _DIANI_LON,
            "key": os.environ["WORLDTIDES_KEY"],
            "days": 14,
        },
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    extremes = data.get("extremes", [])

    _CACHE_FILE.write_text(
        json.dumps({"fetched_at": time.time(), "extremes": extremes})
    )
    return extremes
