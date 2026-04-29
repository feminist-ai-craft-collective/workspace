#!/usr/bin/env python3
"""weather-pulse — fetch NWS forecast and emit a markdown report.

Usage:
  python3 pulse.py                 # report to stdout
  python3 pulse.py --json          # raw NWS bundle (debug)
  python3 pulse.py --set-zip 14817 # one-time setup: resolve zip → write config.json

Reads config.json next to this file. Stdlib only. No deps.
"""
from __future__ import annotations

import json
import math
import os
import re
import sys
import urllib.request
from datetime import datetime, timedelta, timezone

UA = "weather-pulse (https://github.com/anthropics/skills)"
HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(HERE, "config.json")


def load_config() -> dict:
    with open(CONFIG_PATH) as f:
        return json.load(f)


def save_config(cfg: dict) -> None:
    with open(CONFIG_PATH, "w") as f:
        json.dump(cfg, f, indent=2)
        f.write("\n")


def fetch(url: str, accept: str = "application/geo+json") -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": accept})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read())


def set_zip(zip_code: str) -> None:
    """Resolve US zip via zippopotam.us and write to config.json."""
    data = fetch(f"https://api.zippopotam.us/us/{zip_code}", accept="application/json")
    place = data["places"][0]
    cfg = load_config()
    cfg["location"] = {
        "lat": float(place["latitude"]),
        "lon": float(place["longitude"]),
        "label": f"{place['place name']}, {place['state abbreviation']}"
    }
    save_config(cfg)
    print(f"config.json updated: {cfg['location']['label']} ({cfg['location']['lat']}, {cfg['location']['lon']})")


# ---------- helpers ----------

def parse_wind_mph(s: str | None) -> tuple[int, int]:
    if not s:
        return 0, 0
    nums = [int(n) for n in re.findall(r"\d+", s)]
    if not nums:
        return 0, 0
    return min(nums), max(nums)


def wind_chill(temp_f: float, wind_mph: float) -> float:
    if temp_f > 50 or wind_mph <= 3:
        return temp_f
    v16 = wind_mph ** 0.16
    return 35.74 + 0.6215 * temp_f - 35.75 * v16 + 0.4275 * temp_f * v16


def heat_index(temp_f: float, dewpoint_c: float | None) -> float:
    if temp_f < 80 or dewpoint_c is None:
        return temp_f
    t_c = (temp_f - 32) * 5 / 9
    a, b = 17.625, 243.04
    rh = 100 * math.exp((a * dewpoint_c) / (b + dewpoint_c) - (a * t_c) / (b + t_c))
    rh = max(0, min(100, rh))
    t, r = temp_f, rh
    return (-42.379 + 2.04901523*t + 10.14333127*r - 0.22475541*t*r
            - 0.00683783*t*t - 0.05481717*r*r + 0.00122874*t*t*r
            + 0.00085282*t*r*r - 0.00000199*t*t*r*r)


def apparent_temp(temp_f: float, wind_mph: float, dewpoint_c: float | None) -> float:
    if temp_f <= 50:
        return wind_chill(temp_f, wind_mph)
    if temp_f >= 80:
        return heat_index(temp_f, dewpoint_c)
    return temp_f


def sun_times(lat: float, lon: float, date: datetime) -> tuple[datetime, datetime, float]:
    """NOAA solar calc → (sunrise, sunset, daylight_hours) in system-local TZ."""
    doy = date.timetuple().tm_yday
    gamma = 2 * math.pi / 365 * (doy - 1 + (date.hour - 12) / 24)
    eqtime = 229.18 * (0.000075 + 0.001868*math.cos(gamma) - 0.032077*math.sin(gamma)
                       - 0.014615*math.cos(2*gamma) - 0.040849*math.sin(2*gamma))
    decl = (0.006918 - 0.399912*math.cos(gamma) + 0.070257*math.sin(gamma)
            - 0.006758*math.cos(2*gamma) + 0.000907*math.sin(2*gamma)
            - 0.002697*math.cos(3*gamma) + 0.00148*math.sin(3*gamma))
    lat_r = math.radians(lat)
    cos_h = (math.cos(math.radians(90.833)) / (math.cos(lat_r) * math.cos(decl))
             - math.tan(lat_r) * math.tan(decl))
    cos_h = max(-1, min(1, cos_h))
    ha = math.degrees(math.acos(cos_h))
    noon_utc_min = 720 - 4 * lon - eqtime
    sunrise_utc_min = noon_utc_min - 4 * ha
    sunset_utc_min = noon_utc_min + 4 * ha
    midnight_utc = datetime(date.year, date.month, date.day, tzinfo=timezone.utc)
    sunrise = (midnight_utc + timedelta(minutes=sunrise_utc_min)).astimezone()
    sunset = (midnight_utc + timedelta(minutes=sunset_utc_min)).astimezone()
    return sunrise, sunset, (sunset - sunrise).total_seconds() / 3600


def parse_iso(s: str) -> datetime:
    return datetime.fromisoformat(s).astimezone()


def parse_qpf_buckets(raw_grid: dict) -> list[dict]:
    buckets = []
    for v in raw_grid.get("properties", {}).get("quantitativePrecipitation", {}).get("values", []):
        vt = v["validTime"]
        if "/" not in vt:
            continue
        start_str, dur_str = vt.split("/", 1)
        m = re.match(r"PT(\d+)H", dur_str)
        if not m:
            continue
        hours = int(m.group(1))
        start = parse_iso(start_str)
        total_mm = v.get("value") or 0
        buckets.append({
            "start": start, "end": start + timedelta(hours=hours),
            "mm_per_hr": total_mm / hours if hours else 0,
        })
    return buckets


def intensity_label(mm_per_hr: float, cfg: dict) -> str:
    t = cfg["intensity_mm_per_hr"]
    if mm_per_hr < t["drizzle_max"]:
        return "drizzle"
    if mm_per_hr < t["light_steady_max"]:
        return "light/steady"
    if mm_per_hr < t["heavy_max"]:
        return "heavy"
    return "downpour"


def rain_intensity_summary(qpf_buckets, today, cfg) -> str | None:
    today_buckets = [b for b in qpf_buckets if b["start"].date() == today and b["mm_per_hr"] > 0]
    if not today_buckets:
        return None
    peak = max(today_buckets, key=lambda b: b["mm_per_hr"])
    label = intensity_label(peak["mm_per_hr"], cfg)
    if label in ("drizzle", "light/steady"):
        max_label = intensity_label(max(b["mm_per_hr"] for b in today_buckets), cfg)
        return f"{max_label} throughout"
    return f"{label} expected {peak['start'].strftime('%-I%p').lower()}–{peak['end'].strftime('%-I%p').lower()}"


def hour_label(hour: int) -> str:
    if hour == 0: return "12am"
    if hour < 12: return f"{hour}am"
    if hour == 12: return "12pm"
    return f"{hour - 12}pm"


def collapse_blocks(items, pred):
    blocks, start, end = [], None, None
    for h in items:
        hr = h["start"].hour
        if pred(h):
            if start is None: start = hr
            end = hr
        else:
            if start is not None:
                blocks.append((start, end))
                start = None
    if start is not None:
        blocks.append((start, end))
    return blocks


def rain_timing_summary(today_hours, cfg) -> str:
    threshold = cfg["rain_timing"]["wet_threshold_pct"]
    all_day = cfg["rain_timing"]["all_day_threshold_hours"]
    wet = collapse_blocks(today_hours, lambda h: (h.get("precip") or 0) >= threshold)
    if not wet:
        return "no rain expected today"
    total_wet = sum(e - s + 1 for s, e in wet)
    if total_wet >= all_day:
        return "steady rain through the day"
    parts = []
    for s, e in wet:
        parts.append(f"showers around {hour_label(s)}" if s == e else f"showers {hour_label(s)}–{hour_label(e + 1)}")
    return ", ".join(parts)


def best_window(hours, h_start, h_end, cfg) -> str:
    bw = cfg["best_window"]
    in_range = [h for h in hours if h_start <= h["start"].hour < h_end]
    blocks = collapse_blocks(in_range, lambda h: (h.get("precip") or 0) < bw["max_precip_pct"] and h["temp"] >= bw["min_temp_f"])
    if not blocks:
        return "none"
    longest = max(blocks, key=lambda b: b[1] - b[0])
    return f"{longest[0]:02d}:00–{longest[1] + 1:02d}:00"


def vibe_label(highs, cfg) -> tuple[str, str]:
    if not highs:
        return "unknown", "no data"
    v = cfg["vibe"]
    n = len(highs)
    h_max, h_min = max(highs), min(highs)
    rng = h_max - h_min
    swings = [abs(highs[i+1] - highs[i]) for i in range(n - 1)]
    max_swing = max(swings) if swings else 0

    over_90 = sum(1 for h in highs if h >= 90)
    over_hot = sum(1 for h in highs if h >= v["hot_stretch_threshold_f"])
    under_cold = sum(1 for h in highs if h < v["cold_snap_threshold_f"])
    in_smooth = sum(1 for h in highs if v["smooth_sailing_low_f"] <= h <= v["smooth_sailing_high_f"])
    in_mild = sum(1 for h in highs if v["mild_low_f"] <= h <= v["mild_high_f"])
    in_chilly = sum(1 for h in highs if v["chilly_low_f"] <= h <= v["chilly_high_f"])

    highs_str = ", ".join(str(int(h)) for h in highs)

    if over_90 >= v["heatwave_min_days_at_90"]:
        return "heatwave", f"highs {highs_str} — {over_90} days at or above 90°F"
    if over_90 == 1 or over_hot > n / 2:
        return "hot stretch", f"highs {highs_str} — {over_90 or over_hot} hot day(s)"
    if under_cold >= v["cold_snap_min_days"]:
        return "cold snap ahead", f"highs {highs_str} — {under_cold} of {n} days below {v['cold_snap_threshold_f']}°F"
    if max_swing >= v["bumpy_consecutive_swing_f"] or rng >= v["bumpy_week_range_f"]:
        return "bumpy", f"highs {highs_str} — {int(rng)}°F range, biggest swing {int(max_swing)}°F"
    def decade_band(lo, hi):
        return f"{(lo // 10) * 10}s–{(hi // 10) * 10}s"
    if in_smooth > n / 2 and max_swing < v["smooth_sailing_max_swing_f"]:
        return "smooth sailing", f"highs {highs_str} — mostly {decade_band(v['smooth_sailing_low_f'], v['smooth_sailing_high_f'])}, swings under {v['smooth_sailing_max_swing_f']}°F"
    if in_mild > n / 2:
        return "mild", f"highs {highs_str} — {in_mild} of {n} days in the {decade_band(v['mild_low_f'], v['mild_high_f'])}"
    if in_chilly > n / 2:
        return "chilly", f"highs {highs_str} — {in_chilly} of {n} days in the {decade_band(v['chilly_low_f'], v['chilly_high_f'])}"
    return "mixed", f"highs {highs_str} — no dominant pattern"


def rain_label(daily_precip, cfg) -> tuple[str, str]:
    """daily_precip: list of (day_name, max_precip_pct, expected_amount_in, short_forecast)."""
    if not daily_precip:
        return "unknown", "no data"
    rw = cfg["rain_week"]
    pct60 = [d for d in daily_precip if d[1] >= 60]
    pct40 = [d for d in daily_precip if d[1] >= 40]
    pct30 = [d for d in daily_precip if d[1] >= 30]
    pct20 = [d for d in daily_precip if d[1] >= 20]
    real_60 = [d for d in pct60 if d[2] >= rw["heavy_min_amount_in"] or "drizzle" not in d[3].lower()]

    wettest = sorted(daily_precip, key=lambda d: -d[1])[:2]
    wettest_str = ", ".join(f"{d[0]} {d[1]}%" + (f"/{d[2]:.2f}\"" if d[2] > 0 else "") for d in wettest)

    if len(real_60) >= rw["heavy_min_days_60pct"]:
        return "heavy rain week", f"{len(real_60)} days ≥60% with real amounts — {wettest_str}"
    if len(pct40) >= rw["wet_min_days_40pct"] or len(pct60) >= rw["wet_min_days_60pct"]:
        return "wet stretch", f"{len(pct40)} day(s) ≥40%, {len(pct60)} day(s) ≥60% — {wettest_str}"
    if 1 <= len(pct30) <= rw["showers_max_days_30pct"]:
        return "showers", f"{len(pct30)} day(s) ≥30%, mostly light — {wettest_str}"
    if all(d[1] < rw["no_rain_max_pct"] and d[2] == 0 for d in daily_precip):
        return "no rain", f"all 7 days under {rw['no_rain_max_pct']}%"
    return "mostly dry", f"wettest: {wettest_str}"


def compute_flags(today_hours, today_day, today_night, cfg) -> dict:
    f = cfg["flags"]
    today_max_precip = max((h["precip"] for h in today_hours), default=0)
    today_max_gust = max((h["wind_max"] for h in today_hours), default=0)
    high = today_day["temp"] if today_day else None
    low = today_night["temp"] if today_night else None

    mw = f["mowing_ok_today"]
    if today_max_precip >= mw["max_precip_pct"]:
        mowing = ("false", f"max precip {int(today_max_precip)}% (≥{mw['max_precip_pct']}%)")
    elif today_max_gust >= mw["max_gust_mph"]:
        mowing = ("false", f"wind gusts {today_max_gust} mph (≥{mw['max_gust_mph']})")
    else:
        mowing = ("true", "dry and calm")

    rg = f["rain_gear_needed"]
    rg_hit = any((h["precip"] or 0) >= rg["trigger_pct"] for h in today_hours
                 if rg["window_start_hour"] <= h["start"].hour < rg["window_end_hour"])
    rain_gear = ("true" if rg_hit else "false", f"max daytime precip {int(today_max_precip)}%")

    fr = f["frost_overnight"]
    frost = ("true" if (low is not None and low <= fr["max_low_f"]) else "false", f"low {low}°F")

    gr = f["grill_weather"]
    grill_hours = [h for h in today_hours if gr["rain_window_start"] <= h["start"].hour <= gr["rain_window_end"]]
    grill_rain = any((h["precip"] or 0) >= gr["rain_trigger_pct"] for h in grill_hours)
    grill_ok = high is not None and high >= gr["min_high_f"] and not grill_rain
    grill = ("true" if grill_ok else "false",
             f"high {high}°F" + (f", rain {hour_label(gr['rain_window_start'])}–{hour_label(gr['rain_window_end'])}" if grill_rain else ""))

    gw = f["garage_work_ok"]
    garage_ok = high is not None and high >= gw["min_high_f"] and today_max_precip < gw["max_precip_pct"]
    garage = ("true" if garage_ok else "false",
              f"high {high}°F" + (f", precip {int(today_max_precip)}%" if today_max_precip >= gw["max_precip_pct"] else ""))

    return {
        "mowing_ok_today": mowing,
        "rain_gear_needed": rain_gear,
        "frost_overnight": frost,
        "grill_weather": grill,
        "garage_work_ok": garage,
    }


# ---------- main ----------

def main():
    if "--set-zip" in sys.argv:
        idx = sys.argv.index("--set-zip")
        if idx + 1 >= len(sys.argv):
            print("Usage: pulse.py --set-zip <ZIP>", file=sys.stderr)
            sys.exit(1)
        set_zip(sys.argv[idx + 1])
        return

    cfg = load_config()
    lat = cfg["location"]["lat"]
    lon = cfg["location"]["lon"]
    label = cfg["location"]["label"]

    points = fetch(f"https://api.weather.gov/points/{lat},{lon}")
    grid_id = points["properties"]["gridId"]
    grid_x = points["properties"]["gridX"]
    grid_y = points["properties"]["gridY"]

    forecast = fetch(points["properties"]["forecast"])
    hourly = fetch(points["properties"]["forecastHourly"])
    raw_grid = fetch(f"https://api.weather.gov/gridpoints/{grid_id}/{grid_x},{grid_y}")
    alerts = fetch(f"https://api.weather.gov/alerts/active?point={lat},{lon}")

    if "--json" in sys.argv:
        print(json.dumps({"points": points, "forecast": forecast, "hourly": hourly,
                          "raw_grid": raw_grid, "alerts": alerts}, indent=2))
        return

    now = datetime.now().astimezone()
    today = now.date()

    # parse hourly
    hours = []
    for p in hourly["properties"]["periods"]:
        wmin, wmax = parse_wind_mph(p.get("windSpeed"))
        hours.append({
            "start": parse_iso(p["startTime"]),
            "temp": p["temperature"],
            "precip": (p.get("probabilityOfPrecipitation") or {}).get("value") or 0,
            "wind_min": wmin, "wind_max": wmax,
            "wind_dir": p.get("windDirection", ""),
            "short": p.get("shortForecast", ""),
            "dewpoint_c": (p.get("dewpoint") or {}).get("value"),
        })
    today_hours = [h for h in hours if h["start"].date() == today and h["start"] >= now.replace(minute=0, second=0, microsecond=0)]
    next_24h = [h for h in hours if now <= h["start"] < now + timedelta(hours=24)]

    # parse forecast periods
    days_p = []
    for p in forecast["properties"]["periods"]:
        amount = 0.0
        det = p.get("detailedForecast", "")
        m = re.search(r"between\s+([\d.]+)\s+and\s+([\d.]+)\s+of an inch", det)
        if m:
            amount = (float(m.group(1)) + float(m.group(2))) / 2
        else:
            m = re.search(r"around\s+([\d.]+)\s+of an inch", det)
            if m:
                amount = float(m.group(1))
        days_p.append({
            "name": p["name"], "start": parse_iso(p["startTime"]),
            "is_day": p["isDaytime"], "temp": p["temperature"],
            "precip": (p.get("probabilityOfPrecipitation") or {}).get("value") or 0,
            "wind": p.get("windSpeed", ""), "short": p["shortForecast"],
            "detailed": det, "amount_in": amount,
        })

    # roll up to per-day
    daily = {}
    for d in days_p:
        key = d["start"].date() if d["is_day"] else (d["start"] - timedelta(hours=12)).date()
        slot = daily.setdefault(key, {"high": None, "low": None, "max_precip": 0,
                                       "amount_in": 0, "short_day": "", "short_night": "", "name_day": ""})
        if d["is_day"]:
            slot["high"] = d["temp"]
            slot["short_day"] = d["short"]
            slot["name_day"] = d["name"]
        else:
            slot["low"] = d["temp"]
            slot["short_night"] = d["short"]
        slot["max_precip"] = max(slot["max_precip"], d["precip"])
        slot["amount_in"] += d["amount_in"]
    seven = sorted(daily.items())[:7]

    today_day = next((d for d in days_p if d["is_day"] and d["start"].date() == today), None)
    today_night = next((d for d in days_p if not d["is_day"] and d["start"].date() in (today, today + timedelta(days=1)) and d["start"].hour >= 12), None)

    now_h = next((h for h in hours if h["start"] <= now < h["start"] + timedelta(hours=1)), hours[0] if hours else None)
    sunrise, sunset, daylight = sun_times(lat, lon, datetime(today.year, today.month, today.day))

    # wind today
    if today_hours:
        peak_h = max(today_hours, key=lambda h: h["wind_max"])
        non_peak = [h for h in today_hours if h is not peak_h]
        rng_lo = min((h["wind_min"] for h in non_peak), default=peak_h["wind_max"])
        rng_hi = max((h["wind_max"] for h in non_peak), default=peak_h["wind_max"])
        wind_str = f"peak {peak_h['wind_max']} mph around {hour_label(peak_h['start'].hour)}, otherwise {rng_lo}–{rng_hi} mph"
    else:
        wind_str = "unknown"

    # feels-like
    if today_hours:
        actuals = [h["temp"] for h in today_hours]
        apparents = [apparent_temp(h["temp"], (h["wind_min"] + h["wind_max"]) / 2, h["dewpoint_c"]) for h in today_hours]
        gaps = [abs(a - p) for a, p in zip(actuals, apparents)]
        max_gap = max(gaps)
        layering = max_gap >= cfg["feels_like"]["layering_swing_f"]
        feels_str = (f"actual {int(max(actuals))}/{int(min(actuals))}, "
                     f"apparent {int(round(max(apparents)))}/{int(round(min(apparents)))} — "
                     f"swing of {int(round(max_gap))}°F (layering matters: {'yes' if layering else 'no'})")
    else:
        feels_str = "unknown"

    qpf_buckets = parse_qpf_buckets(raw_grid)
    rain_intensity_str = rain_intensity_summary(qpf_buckets, today, cfg)
    rain_timing_str = rain_timing_summary(today_hours, cfg)
    morning_win = best_window(today_hours, cfg["best_window"]["morning_start"], cfg["best_window"]["morning_end"], cfg)
    afternoon_win = best_window(today_hours, cfg["best_window"]["afternoon_start"], cfg["best_window"]["afternoon_end"], cfg)

    highs = [d["high"] for k, d in seven if d["high"] is not None]
    vibe_lbl, vibe_reason = vibe_label(highs, cfg)
    rain_data = [(d["name_day"] or k.strftime("%A"), d["max_precip"], d["amount_in"],
                  d["short_day"] + " " + d["short_night"]) for k, d in seven]
    rain_lbl, rain_reason = rain_label(rain_data, cfg)

    flags = compute_flags(today_hours, today_day, today_night, cfg)

    feats = alerts.get("features", [])
    alerts_str = "none" if not feats else f"{len(feats)} active: " + "; ".join(
        f.get("properties", {}).get("headline", "alert") for f in feats)

    # build output
    out = []
    out.append(f"WEATHER PULSE — {label} — {now.isoformat(timespec='seconds')}")
    out.append("")
    out.append(f"[ALERTS] {alerts_str}")
    out.append("")
    if now_h:
        out.append(f"NOW: {now_h['temp']}°F, {now_h['short'].lower()}, wind {now_h['wind_dir']} {now_h['wind_max']} mph")
    out.append("")
    if today_day:
        out.append(f"TODAY: {today_day['temp']}°F. {today_day['short']}. Precip {today_day['precip']}%.")
    if today_night:
        out.append(f"TONIGHT: {today_night['temp']}°F. {today_night['short']}. Precip {today_night['precip']}%.")
    out.append("")
    out.append(f"SUN: rise {sunrise.strftime('%H:%M')}, set {sunset.strftime('%H:%M')} — {daylight:.1f}h daylight")
    out.append(f"RAIN TIMING: {rain_timing_str}")
    if rain_intensity_str:
        out.append(f"RAIN INTENSITY: {rain_intensity_str}")
    out.append(f"WIND TODAY: {wind_str}")
    out.append(f"FEELS-LIKE: {feels_str}")
    out.append("")
    out.append("BEST WINDOWS:")
    out.append(f"  Morning: {morning_win}")
    out.append(f"  Afternoon: {afternoon_win}")
    out.append("")
    out.append("NEXT 24H (hourly):")
    for h in next_24h[::3]:
        out.append(f"  {h['start'].strftime('%H:%M')} — {h['temp']}°F, {h['precip']}%, {h['wind_dir']} {h['wind_max']}, {h['short'].lower()}")
    out.append("")
    out.append("7-DAY:")
    for k, d in seven:
        name = d["name_day"] or k.strftime("%A")
        amt = f"/{d['amount_in']:.2f}\"" if d["amount_in"] > 0 else ""
        out.append(f"  {name} — {d['high']}/{d['low']}, {d['short_day'].lower()}, precip {d['max_precip']}%{amt}")
    out.append("")
    out.append(f"7-DAY VIBE: {vibe_lbl} — {vibe_reason}")
    out.append(f"7-DAY RAIN: {rain_lbl} — {rain_reason}")
    out.append("")
    out.append("FLAGS:")
    for k, (val, reason) in flags.items():
        out.append(f"  {k}: {val}" + (f" — {reason}" if reason else ""))
    out.append("")
    notes = []
    for d in (today_day, today_night):
        if d:
            m = re.search(r"before\s+(\d+\s*(am|pm))", d["detailed"].lower())
            if m:
                tag = "today" if d is today_day else "overnight"
                notes.append(f"rain mainly before {m.group(1)} {tag}")
    out.append(f"NOTES: {'; '.join(notes) if notes else '(none)'}")

    print("\n".join(out))


if __name__ == "__main__":
    main()
