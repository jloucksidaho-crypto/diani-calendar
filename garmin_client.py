import os
import time

from garminconnect import Garmin

_cache: dict = {"activities": [], "fetched_at": 0}
_CACHE_TTL = 1800  # 30 minutes
_api = None


def _get_client() -> Garmin:
    global _api
    if _api:
        return _api

    email = os.environ["GARMIN_EMAIL"]
    password = os.environ["GARMIN_PASSWORD"]

    _api = Garmin(email, password)
    _api.login()
    return _api


def get_activities(count: int = 60) -> list:
    global _api
    if _cache["activities"] and time.time() - _cache["fetched_at"] < _CACHE_TTL:
        return _cache["activities"]

    try:
        client = _get_client()
        activities = client.get_activities(0, count)
    except Exception:
        # Session may have expired — force a fresh login on next request
        _api = None
        raise

    _cache["activities"] = activities
    _cache["fetched_at"] = time.time()
    return activities
