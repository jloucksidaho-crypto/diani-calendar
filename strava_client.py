import os
import time

import requests

_TOKEN_URL = "https://www.strava.com/oauth/token"
_ACTIVITIES_URL = "https://www.strava.com/api/v3/athlete/activities"

_token_cache: dict = {"access_token": None, "expires_at": 0}


def _get_access_token() -> str:
    if _token_cache["access_token"] and time.time() < _token_cache["expires_at"] - 60:
        return _token_cache["access_token"]

    resp = requests.post(
        _TOKEN_URL,
        data={
            "client_id": os.environ["STRAVA_CLIENT_ID"],
            "client_secret": os.environ["STRAVA_CLIENT_SECRET"],
            "grant_type": "refresh_token",
            "refresh_token": os.environ["STRAVA_REFRESH_TOKEN"],
        },
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    _token_cache["access_token"] = data["access_token"]
    _token_cache["expires_at"] = data["expires_at"]
    return data["access_token"]


def get_activities(per_page: int = 60) -> list:
    token = _get_access_token()
    resp = requests.get(
        _ACTIVITIES_URL,
        headers={"Authorization": f"Bearer {token}"},
        params={"per_page": per_page},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()
