import json
import os
import time
from pathlib import Path

from garminconnect import Garmin

_cache: dict = {"activities": [], "fetched_at": 0}
_CACHE_TTL = 1800  # 30 minutes
_api = None
_GARTH_DIR = Path("/tmp/garth_diani")


def _get_client() -> Garmin:
    global _api
    if _api:
        return _api

    tokens_json = os.environ.get("GARMIN_TOKENS")
    if not tokens_json:
        raise RuntimeError("GARMIN_TOKENS environment variable not set. Run setup_garmin.py.")

    tokens = json.loads(tokens_json)

    # Write token files to a directory that persists for the server process lifetime.
    # Using a fixed path (not a managed tempdir) so garth can read/write tokens as needed.
    _GARTH_DIR.mkdir(parents=True, exist_ok=True)
    (_GARTH_DIR / "oauth1_token.json").write_text(json.dumps(tokens["oauth1"]))
    (_GARTH_DIR / "oauth2_token.json").write_text(json.dumps(tokens["oauth2"]))

    _api = Garmin()
    _api.garth.load(str(_GARTH_DIR))

    return _api


def get_activities(count: int = 60) -> list:
    global _api
    if _cache["activities"] and time.time() - _cache["fetched_at"] < _CACHE_TTL:
        return _cache["activities"]

    client = _get_client()
    activities = client.get_activities(0, count)

    _cache["activities"] = activities
    _cache["fetched_at"] = time.time()
    return activities
