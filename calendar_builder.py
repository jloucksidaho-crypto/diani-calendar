from datetime import datetime, timedelta

import pytz
from icalendar import Calendar, Event

_NAIROBI = pytz.timezone("Africa/Nairobi")

_SPORT_EMOJI = {
    "Run": "🏃",
    "TrailRun": "🏃",
    "Ride": "🚴",
    "MountainBikeRide": "🚵",
    "VirtualRide": "🚴",
    "Swim": "🏊",
    "Walk": "🚶",
    "Hike": "🥾",
    "WeightTraining": "🏋️",
    "Yoga": "🧘",
    "Surf": "🏄",
    "Kayaking": "🚣",
    "StandUpPaddling": "🏄",
    "Workout": "💪",
    "CrossFit": "💪",
    "Tennis": "🎾",
    "Soccer": "⚽",
    "Golf": "⛳",
    "Rowing": "🚣",
    "Kitesurf": "🪁",
    "Windsurf": "🏄",
    "Snorkeling": "🤿",
}


def _fmt_duration(seconds: float) -> str:
    h, m = int(seconds // 3600), int((seconds % 3600) // 60)
    return f"{h}h {m:02d}m" if h else f"{m}m"


def _fmt_distance(meters: float) -> str:
    return f"{meters / 1000:.2f} km" if meters >= 1000 else f"{int(meters)} m"


def _base_calendar(name: str, desc: str, ttl_minutes: int) -> Calendar:
    cal = Calendar()
    cal.add("prodid", f"-//Diani Calendar//{name}//EN")
    cal.add("version", "2.0")
    cal.add("x-wr-calname", name)
    cal.add("x-wr-caldesc", desc)
    cal.add("x-wr-timezone", "Africa/Nairobi")
    cal.add("refresh-interval;value=duration", f"PT{ttl_minutes}M")
    cal.add("x-published-ttl", f"PT{ttl_minutes}M")
    return cal


def build_fitness_cal(activities: list) -> Calendar:
    cal = _base_calendar(
        "Fitness Activities",
        "Strava workouts synced automatically",
        30,
    )

    for activity in activities:
        sport = activity.get("sport_type") or activity.get("type") or "Workout"
        emoji = _SPORT_EMOJI.get(sport, "🏅")

        distance = activity.get("distance", 0)
        moving_time = activity.get("moving_time", 0)
        elapsed_time = activity.get("elapsed_time", 0) or moving_time
        avg_hr = activity.get("average_heartrate")
        max_hr = activity.get("max_heartrate")
        calories = activity.get("calories") or activity.get("kilojoules")
        elevation = activity.get("total_elevation_gain")
        strava_id = activity.get("id")
        activity_name = activity.get("name", sport)

        # Compact summary line shown as the calendar event title
        summary_parts = [f"{emoji} {sport}"]
        if distance:
            summary_parts.append(_fmt_distance(distance))
        if moving_time:
            summary_parts.append(_fmt_duration(moving_time))
        if avg_hr:
            summary_parts.append(f"HR {int(avg_hr)}")
        summary = " · ".join(summary_parts)

        # Full detail in the event description
        desc_lines = [f"Name: {activity_name}"]
        if distance:
            desc_lines.append(f"Distance: {_fmt_distance(distance)}")
        if moving_time:
            desc_lines.append(f"Moving time: {_fmt_duration(moving_time)}")
        if elapsed_time and elapsed_time != moving_time:
            desc_lines.append(f"Elapsed time: {_fmt_duration(elapsed_time)}")
        if elevation:
            desc_lines.append(f"Elevation gain: {int(elevation)} m")
        if avg_hr:
            desc_lines.append(f"Avg heart rate: {int(avg_hr)} bpm")
        if max_hr:
            desc_lines.append(f"Max heart rate: {int(max_hr)} bpm")
        if calories:
            desc_lines.append(f"Calories: {int(calories)}")
        if strava_id:
            desc_lines.append(f"\nhttps://www.strava.com/activities/{strava_id}")

        start_str = activity.get("start_date")
        if not start_str:
            continue
        start_dt = datetime.fromisoformat(start_str.replace("Z", "+00:00")).astimezone(_NAIROBI)
        end_dt = start_dt + timedelta(seconds=elapsed_time)

        event = Event()
        event.add("summary", summary)
        event.add("dtstart", start_dt)
        event.add("dtend", end_dt)
        event.add("description", "\n".join(desc_lines))
        event.add("uid", f"strava-{strava_id}@diani-calendar")
        cal.add_component(event)

    return cal


def build_tides_cal(extremes: list) -> Calendar:
    cal = _base_calendar(
        "Diani Beach Tides",
        "Daily high and low tides for Diani Beach, Kenya",
        360,
    )

    for tide in extremes:
        tide_type = tide.get("type", "")
        height = tide.get("height", 0.0)
        dt_unix = tide.get("dt")
        if not dt_unix:
            continue

        dt = datetime.fromtimestamp(dt_unix, tz=pytz.utc).astimezone(_NAIROBI)

        if tide_type == "High":
            emoji, label = "🌊", "High Tide"
        else:
            emoji, label = "🏖️", "Low Tide"

        summary = f"{emoji} {label}: {height:.2f} m"
        description = (
            f"{label} — Diani Beach, Kenya\n"
            f"Height: {height:.2f} m\n"
            f"Time: {dt.strftime('%H:%M %Z')}"
        )

        event = Event()
        event.add("summary", summary)
        event.add("dtstart", dt)
        event.add("dtend", dt + timedelta(minutes=30))
        event.add("description", description)
        event.add("uid", f"tide-{dt_unix}@diani-calendar")
        cal.add_component(event)

    return cal
