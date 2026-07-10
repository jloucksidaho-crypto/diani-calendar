import os
import time
from datetime import datetime, timezone

import requests

_BASE_URL = "https://intervals.icu/api/v1/athlete"

_cache: dict = {"activities": [], "fetched_at": 0}
_CACHE_TTL = 1800  # 30 minutes


def get_activities(count: int = 60) -> list:
    if _cache["activities"] and time.time() - _cache["fetched_at"] < _CACHE_TTL:
        return _cache["activities"]

    athlete_id = os.environ["INTERVALS_ATHLETE_ID"]
    api_key = os.environ["INTERVALS_API_KEY"]

    resp = requests.get(
        f"{_BASE_URL}/{athlete_id}/activities",
        auth=("API_KEY", api_key),
        params={"limit": count},
        timeout=15,
    )
    resp.raise_for_status()
    activities = resp.json()

    _cache["activities"] = activities
    _cache["fetched_at"] = time.time()
    return activities
