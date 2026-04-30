import os
import urllib.parse

import requests
from flask import Flask, Response, redirect, request, url_for

from calendar_builder import build_fitness_cal, build_tides_cal
from strava_client import get_activities
from tides_client import get_tides

app = Flask(__name__)


@app.route("/")
def index():
    base = request.host_url.rstrip("/")
    return f"""
    <html>
    <head><title>Diani Calendar Feeds</title></head>
    <body style="font-family: -apple-system, sans-serif; max-width: 640px; margin: 60px auto; padding: 20px; color: #222;">
      <h2>Diani Calendar Feeds</h2>
      <p>Two live calendar feeds ready to subscribe to in Apple Calendar:</p>
      <table style="border-collapse:collapse; width:100%;">
        <tr>
          <td style="padding:10px 0;"><strong>Fitness (Strava)</strong></td>
          <td><code style="background:#f4f4f4; padding:4px 8px; border-radius:4px;">{base}/fitness.ics</code></td>
        </tr>
        <tr>
          <td style="padding:10px 0;"><strong>Diani Beach Tides</strong></td>
          <td><code style="background:#f4f4f4; padding:4px 8px; border-radius:4px;">{base}/tides.ics</code></td>
        </tr>
      </table>
      <hr style="margin:30px 0;">
      <h3>How to subscribe</h3>
      <p><strong>Mac:</strong> File &rarr; New Calendar Subscription &rarr; paste URL</p>
      <p><strong>iPhone/iPad:</strong> Settings &rarr; Calendar &rarr; Accounts &rarr; Add Account &rarr; Other &rarr; Add Subscribed Calendar</p>
      <hr style="margin:30px 0;">
      <p style="color:#666; font-size:0.9em;">
        Fitness feed refreshes every 30 minutes &nbsp;|&nbsp; Tides feed refreshes every 6 hours
      </p>
    </body>
    </html>
    """


@app.route("/fitness.ics")
def fitness():
    activities = get_activities()
    cal = build_fitness_cal(activities)
    return Response(
        cal.to_ical(),
        mimetype="text/calendar",
        headers={"Content-Disposition": "inline; filename=fitness.ics"},
    )


@app.route("/tides.ics")
def tides():
    tides_data = get_tides()
    cal = build_tides_cal(tides_data)
    return Response(
        cal.to_ical(),
        mimetype="text/calendar",
        headers={"Content-Disposition": "inline; filename=tides.ics"},
    )


@app.route("/strava/auth")
def strava_auth():
    client_id = os.environ.get("STRAVA_CLIENT_ID", "")
    callback_url = url_for("strava_callback", _external=True)
    params = urllib.parse.urlencode(
        {
            "client_id": client_id,
            "redirect_uri": callback_url,
            "response_type": "code",
            "scope": "activity:read_all",
        }
    )
    return redirect(f"https://www.strava.com/oauth/authorize?{params}")


@app.route("/strava/callback")
def strava_callback():
    code = request.args.get("code")
    if not code:
        return "Authorization failed — no code received from Strava.", 400

    resp = requests.post(
        "https://www.strava.com/oauth/token",
        data={
            "client_id": os.environ["STRAVA_CLIENT_ID"],
            "client_secret": os.environ["STRAVA_CLIENT_SECRET"],
            "code": code,
            "grant_type": "authorization_code",
        },
        timeout=15,
    )
    resp.raise_for_status()
    data = resp.json()
    refresh_token = data.get("refresh_token", "")
    athlete = data.get("athlete", {})
    name = f"{athlete.get('firstname', '')} {athlete.get('lastname', '')}".strip()

    return f"""
    <html>
    <body style="font-family: -apple-system, sans-serif; max-width: 640px; margin: 60px auto; padding: 20px;">
      <h2>Strava Connected!</h2>
      <p>Authorized as: <strong>{name}</strong></p>
      <p>Copy the refresh token below and paste it as <code>STRAVA_REFRESH_TOKEN</code>
         in your Render environment variables, then redeploy:</p>
      <pre style="background:#f0f0f0; padding:16px; border-radius:6px;
                  word-break:break-all; font-size:0.85em;">{refresh_token}</pre>
      <p><a href="/">Back to calendar feeds</a></p>
    </body>
    </html>
    """


if __name__ == "__main__":
    app.run(debug=False, port=int(os.environ.get("PORT", 5000)))
