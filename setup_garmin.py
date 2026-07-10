"""
Run this once locally to authenticate with Garmin and generate
the GARMIN_TOKENS value for your Render environment variables.

Usage:
    python3 setup_garmin.py
"""

import getpass
import json
import tempfile
from pathlib import Path

from garminconnect import Garmin


def main():
    print("Garmin Authentication Setup")
    print("-" * 30)
    email = input("Garmin email: ")
    password = getpass.getpass("Garmin password: ")

    print("\nLogging in to Garmin...")
    try:
        api = Garmin(email, password)
        api.login()
    except Exception as e:
        if "MFA" in str(e) or "2FA" in str(e) or "code" in str(e).lower():
            code = input("Enter the 2FA code sent to your email/phone: ")
            api.resume_login(code)
        else:
            raise

    # Save tokens to a temp directory then read them back
    with tempfile.TemporaryDirectory() as tmpdir:
        api.garth.dump(tmpdir)
        oauth1 = json.loads((Path(tmpdir) / "oauth1_token.json").read_text())
        oauth2 = json.loads((Path(tmpdir) / "oauth2_token.json").read_text())

    combined = json.dumps({"oauth1": oauth1, "oauth2": oauth2})

    print("\n✅ Login successful!")
    print("\n" + "=" * 60)
    print("Copy everything between the lines below and paste it")
    print("as GARMIN_TOKENS in your Render environment variables:")
    print("=" * 60)
    print(combined)
    print("=" * 60)
    print("\nOnce saved in Render, your fitness calendar will work again.")


if __name__ == "__main__":
    main()
