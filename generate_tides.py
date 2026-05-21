"""
Run this script once to generate tide data for Diani Beach.
It saves the results to tides_data.json so the app never needs to call
the WorldTides API again during normal operation.

Usage:
    WORLDTIDES_KEY=your_key python3 generate_tides.py
"""

import json
import os
import sys
import time
from datetime import datetime, timezone

import requests

API_URL = "https://www.worldtides.info/api/v3"
LAT = -4.3167
LON = 39.5667
OUTPUT_FILE = os.path.join(os.path.dirname(__file__), "tides_data.json")

# Try these day ranges in order — use the longest one the API accepts
DAY_ATTEMPTS = [365, 180, 90, 60, 28]


def main():
    key = os.environ.get("WORLDTIDES_KEY")
    if not key and len(sys.argv) > 1:
        key = sys.argv[1]
    if not key:
        print("ERROR: WorldTides API key not found.")
        print("Run as:  WORLDTIDES_KEY=your_key python3 generate_tides.py")
        sys.exit(1)

    extremes = []
    days_fetched = 0

    for days in DAY_ATTEMPTS:
        print(f"Trying {days} days...")
        # 'extremes' must be a bare flag in the URL — not extremes=value
        url = f"{API_URL}?extremes&lat={LAT}&lon={LON}&key={key}&days={days}"
        resp = requests.get(url, timeout=30)
        if resp.status_code == 200:
            data = resp.json()
            extremes = data.get("extremes", [])
            days_fetched = days
            break
        else:
            print(f"  {days} days returned {resp.status_code}, trying fewer...")

    if not extremes:
        print("ERROR: Could not fetch tide data. Check your API key and credits.")
        sys.exit(1)

    output = {
        "generated_at": time.time(),
        "generated_date": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "lat": LAT,
        "lon": LON,
        "days": days_fetched,
        "count": len(extremes),
        "extremes": extremes,
    }

    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f)

    first = datetime.fromtimestamp(extremes[0]["dt"]).strftime("%d %b %Y")
    last = datetime.fromtimestamp(extremes[-1]["dt"]).strftime("%d %b %Y")

    print()
    print(f"  Saved {len(extremes)} tide events to tides_data.json")
    print(f"  Coverage: {first}  to  {last}")
    print()
    print("Next steps:")
    print("  1. Open GitHub Desktop")
    print("  2. You will see tides_data.json listed — commit and push it")
    print("  3. Render redeploys automatically — no more credits ever used")
    print()
    print("Run this script again when data is getting close to expiry.")


if __name__ == "__main__":
    main()
