import os
import time

import requests

_API_URL = "https://www.worldtides.info/api/v3"
_DIANI_LAT = -4.3167
_DIANI_LON = 39.5667
_CACHE_TTL = 86400  # re-fetch once per day at most

# In-memory cache — survives across requests within a single server session.
# One API call per server restart (Render free tier restarts after inactivity),
# which typically means 1-3 calls per day rather than one per 6-hour cache miss.
_cache: dict = {"fetched_at": 0, "extremes": []}


def get_tides() -> list:
    if _cache["extremes"] and time.time() - _cache["fetched_at"] < _CACHE_TTL:
        return _cache["extremes"]

    resp = requests.get(
        _API_URL,
        params={
            "extremes": "",
            "lat": _DIANI_LAT,
            "lon": _DIANI_LON,
            "key": os.environ["WORLDTIDES_KEY"],
            "days": 30,  # fetch 30 days at once — one call covers a full month
        },
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()

    _cache["extremes"] = data.get("extremes", [])
    _cache["fetched_at"] = time.time()
    return _cache["extremes"]
