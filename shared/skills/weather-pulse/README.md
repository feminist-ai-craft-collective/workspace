# weather-pulse

A Claude skill that fetches a National Weather Service forecast for a configured US location and writes a structured markdown report to a folder. Designed to run on a cron 1–2× a day so other Claude agents can consume the latest report when planning.

## What you get

Each run produces one markdown file containing:

- **Now / today / tonight** — temp, conditions, wind, precip%
- **Sun** — sunrise, sunset, daylight hours (computed locally; NWS doesn't provide them)
- **Rain timing** — plain-English summary of *when* rain falls (e.g. "dry until 2pm, showers 2–7pm")
- **Rain intensity** — `drizzle` / `light/steady` / `heavy` / `downpour`, with a time window when it crosses heavy. Skipped when there's no rain.
- **Wind today** — peak gust + typical range
- **Feels-like swing** — actual vs. apparent (wind chill below 50°F, heat index above 80°F), with `layering matters: yes/no`
- **Best windows** — longest dry+warm block in morning (6am–12pm) and afternoon (12pm–8pm)
- **Next 24h hourly** — every 3 hours
- **7-day raw** — high/low, conditions, max precip%, expected amounts in inches (kept for hindcasting forecast accuracy)
- **7-day vibe** — temperature character: `heatwave` / `hot stretch` / `cold snap ahead` / `bumpy` / `smooth sailing` / `mild` / `chilly` / `mixed`
- **7-day rain** — precipitation character: `heavy rain week` / `wet stretch` / `showers` / `mostly dry` / `no rain`
- **Flags** — opinionated planning booleans (`mowing_ok_today`, `garage_work_ok`, `frost_overnight`, etc.)
- **Notes** — timing callouts pulled from NWS detailed text ("rain mainly before 4am")

Each label/flag includes its reasoning so you can audit the verdict.

## Files

```
weather-pulse/
├── SKILL.md       # Skill definition (Claude reads this)
├── pulse.py       # Python CLI that does the actual work
├── config.json    # Location + all thresholds (the only file most users edit)
└── README.md      # This file
```

## Install

If you're consuming this from the FAICC shared skills folder, you have two options:

**Option A: Reference in place** — point your project's `CLAUDE.md` at this skill's `SKILL.md`:
```markdown
## Skills Available
- Weather pulse: `../../shared/skills/weather-pulse/SKILL.md`
```
This works if your Claude has filesystem access and you're okay with the shared `config.json`.

**Option B: Copy into your project** — duplicate the folder so you can customize `config.json` without touching the shared version. This is what most contributors will want.

Either way, after install:

```bash
# Set your US location (one-time)
/usr/bin/python3 path/to/weather-pulse/pulse.py --set-zip 11201

# Pick where reports get stored — edit config.json:
"local_archive_dir": "/path/to/your/weather-reports"
```

## Requirements

- Python 3.9+. Stdlib only — no `pip install`.
- A Claude environment that can run `Bash`, `Write`, and `Read` tools (Claude Code, or any agent harness that exposes those).
- US location. NWS is the only data source; international support would require swapping the fetch layer.
- macOS users: if you installed Python from python.org and hit `SSL: CERTIFICATE_VERIFY_FAILED`, run `/Applications/Python\ 3.X/Install\ Certificates.command` or use `/usr/bin/python3` (the SKILL.md specifies the latter).

## Configuration

Everything tunable lives in **`config.json`** — one file, no Python edits needed for normal use.

### Quick setup by zip code

```bash
/usr/bin/python3 path/to/weather-pulse/pulse.py --set-zip 11201
```

Resolves the zip via `zippopotam.us` (free, no auth) and writes `lat`, `lon`, and `label` to `config.json`. Timezone is taken from the OS at runtime — no need to set it.

### What's in config.json

| Section | What it controls |
|---------|------------------|
| `location` | lat, lon, label (used in report header) |
| `local_archive_dir` | default folder for reports when no path is passed in args. Per-invocation paths still override. Set to `""` to require an explicit path each time. |
| `intensity_mm_per_hr` | drizzle/light/heavy/downpour thresholds |
| `vibe` | 7-day temperature label thresholds (heatwave, cold snap, bumpy, smooth sailing, mild, chilly) |
| `rain_week` | 7-day precipitation label thresholds (heavy rain week, wet stretch, showers, mostly dry, no rain) |
| `best_window` | temp + precip thresholds for "good outdoor block" + morning/afternoon hour ranges |
| `rain_timing` | wet-hour threshold and "all-day rain" length |
| `feels_like` | swing threshold for `layering matters: yes` |
| `flags.mowing_ok_today` etc. | per-flag tuning (max precip%, min/max temps, gust limits, time windows) |

Edit values, save, run. No restart needed.

### Tuning preferences — worked examples

Open `config.json`, find the relevant section, change the number, save. The next run picks it up — no restart, no caching, no Python edits.

**"I think the rain-gear flag is too eager. Don't tell me to grab a coat unless it's at least 50% chance during my outdoor hours."**
```json
"flags": {
  "rain_gear_needed": {
    "trigger_pct": 50,
    "window_start_hour": 8,
    "window_end_hour": 20
  }
}
```

**"I'd mow even if there's a small chance of rain. And I run a lighter mower so wind matters less."**
```json
"flags": {
  "mowing_ok_today": {
    "max_precip_pct": 50,
    "max_gust_mph": 35
  }
}
```

**"Down here in Florida, 'mild' should be 60s–70s, not 50s–60s, and 'smooth sailing' starts at 75."**
```json
"vibe": {
  "smooth_sailing_low_f": 75,
  "smooth_sailing_high_f": 89,
  "mild_low_f": 60,
  "mild_high_f": 79
}
```

**"I want my outdoor work window to require 60°F, not 45°F."**
```json
"best_window": {
  "min_temp_f": 60,
  "max_precip_pct": 20,
  "morning_start": 6,
  "morning_end": 12,
  "afternoon_start": 12,
  "afternoon_end": 20
}
```

**"The default flags don't match my life. I don't have a lawn or a grill."**
The shipped flags (`mowing_ok_today`, `grill_weather`, `garage_work_ok`) reflect a specific household. Either:
- Ignore the ones you don't care about — the report just lists them, your downstream agent decides which to act on.
- Replace them: edit `compute_flags()` in `pulse.py` to remove or rename, and adjust the matching block in `config.json`. Sample replacements: `dog_walk_window`, `bike_to_work`, `commute_ok_today`, `kids_outside_recess`, `studio_window_open` (for ventilation), etc.

If a config value is missing or invalid, the script will throw a `KeyError` at runtime — the fix is in the error message.

## Usage

**Fetch mode** — hit NWS, derive flags, write a report file:
```
/weather-pulse                            # → uses local_archive_dir from config
/weather-pulse /abs/path/to/reports       # → writes to that folder
```

**Recall mode** — read the latest stored report without touching NWS (cheap, instant; for agents that want weather context for planning):
```
/weather-pulse recall                     # → latest from configured folder
/weather-pulse recall /abs/path/to/reports   # → latest from that folder
```

Recall mode prepends a staleness warning if the latest report is >8h old, but does not auto-refresh.

**Path resolution**: args path > `config.local_archive_dir` > hard error. Never silently guesses.

## How the data flows

```
api.weather.gov  →  pulse.py  →  stdout (markdown report)
                                   ↓
              SKILL.md instructs Claude to:
                   • Write to {dir}/YYYY-MM-DD-HHMM.md
```

The skill itself does no reasoning about the data. Determinism lives in `pulse.py`.

## NWS endpoints used

- `https://api.weather.gov/points/{lat},{lon}` — resolves the gridpoint
- `https://api.weather.gov/gridpoints/{office}/{x},{y}/forecast` — 7-day periods
- `https://api.weather.gov/gridpoints/{office}/{x},{y}/forecast/hourly` — next ~156h hourly
- `https://api.weather.gov/gridpoints/{office}/{x},{y}` — raw gridded data (for QPF mm/hour)
- `https://api.weather.gov/alerts/active?point={lat},{lon}` — watches/warnings/advisories

The User-Agent header is set to comply with NWS's API policy.

## Debugging

```
/usr/bin/python3 path/to/weather-pulse/pulse.py --json
```

Dumps the raw NWS bundle (points + forecast + hourly + alerts + raw_grid) so you can inspect what the upstream is saying before the labels get applied.

## Limitations

- US-only (NWS).
- One fixed location per `config.json`. To support multiple locations, copy the folder under different names.
- Forecast intensity (`heavy`/`downpour`) uses gridded QPF in 3- or 6-hour buckets, so the time window granularity isn't hour-precise.
- "Apparent temperature" is computed locally because NWS hourly doesn't expose it; outside the wind chill (≤50°F) or heat index (≥80°F) ranges, apparent = actual.
- Period-level "expected amount in inches" is parsed from NWS detailed text via regex; word-form amounts ("between a half and three quarters of an inch") aren't extracted, only numeral forms.

## Origin

Built by a contributor for personal day-planning, then generalized for the FAICC shared skills folder. Filed under `shared/skills/` so anyone can adopt and customize.
