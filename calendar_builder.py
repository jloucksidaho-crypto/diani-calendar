from datetime import datetime, timedelta, timezone

import pytz
from icalendar import Calendar, Event

_NAIROBI = pytz.timezone("Africa/Nairobi")

_SPORT_EMOJI = {
    # Garmin type keys (snake_case)
    "running": "🏃",
    "trail_running": "🏃",
    "cycling": "🚴",
    "mountain_biking": "🚵",
    "virtual_cycling": "🚴",
    "swimming": "🏊",
    "open_water_swimming": "🏊",
    "walking": "🚶",
    "hiking": "🥾",
    "strength_training": "🏋️",
    "yoga": "🧘",
    "surfing": "🏄",
    "kayaking": "🚣",
    "stand_up_paddleboarding": "🏄",
    "fitness_equipment": "💪",
    "tennis": "🎾",
    "soccer": "⚽",
    "golf": "⛳",
    "rowing": "🚣",
    "kiteboarding": "🪁",
    "windsurfing": "🏄",
    "snorkeling": "🤿",
    "breathwork": "🧘",
    "indoor_cardio": "💪",
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
        "Garmin workouts synced via Intervals.icu",
        30,
    )

    for activity in activities:
        # Garmin field names via garminconnect library
        type_info = activity.get("activityType") or {}
        sport_key = type_info.get("typeKey") or "running"
        sport_label = sport_key.replace("_", " ").title()
        emoji = _SPORT_EMOJI.get(sport_key, "🏅")

        activity_id = activity.get("activityId", "")
        activity_name = activity.get("activityName") or sport_label
        distance = activity.get("distance") or 0
        moving_time = activity.get("movingDuration") or activity.get("duration") or 0
        elapsed_time = activity.get("duration") or moving_time
        avg_hr = activity.get("averageHR")
        max_hr = activity.get("maxHR")
        calories = activity.get("calories")
        elevation = activity.get("elevationGain")

        # Compact summary line shown as the calendar event title
        summary_parts = [f"{emoji} {sport_label}"]
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
        if activity_id:
            desc_lines.append(f"\nhttps://connect.garmin.com/modern/activity/{activity_id}")

        local_str = activity.get("startTimeLocal")
        gmt_str = activity.get("startTimeGMT")
        if not local_str and not gmt_str:
            continue

        if local_str and gmt_str:
            local_dt = datetime.strptime(local_str, "%Y-%m-%d %H:%M:%S")
            gmt_dt = datetime.strptime(gmt_str, "%Y-%m-%d %H:%M:%S")
            start_dt = local_dt.replace(tzinfo=timezone(local_dt - gmt_dt))
        elif local_str:
            start_dt = _NAIROBI.localize(datetime.strptime(local_str, "%Y-%m-%d %H:%M:%S"))
        else:
            start_dt = pytz.utc.localize(datetime.strptime(gmt_str, "%Y-%m-%d %H:%M:%S"))
        end_dt = start_dt + timedelta(seconds=elapsed_time)

        event = Event()
        event.add("summary", summary)
        event.add("dtstart", start_dt)
        event.add("dtend", end_dt)
        event.add("description", "\n".join(desc_lines))
        event.add("uid", f"garmin-{activity_id}@diani-calendar")
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
