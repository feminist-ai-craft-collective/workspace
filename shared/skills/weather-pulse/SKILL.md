---
name: weather-pulse
description: Fetch a fresh National Weather Service forecast for a configured US location and write it as a timestamped markdown file, OR recall the most recent stored report without fetching. Designed to run on a cron 1–2× per day so other agents can consume the latest weather context for planning.
---

# /weather-pulse — Fetch or recall a weather report

Two modes:
- **Fetch** (default): hit NWS, derive flags/labels, write a markdown report to disk.
- **Recall**: read the most recent stored report without touching NWS. Cheap, instant.

Mode is determined by the args. The `recall` keyword (anywhere in args) switches to read-only.

## Args matrix

| Args | Mode | Behavior |
|------|------|----------|
| _(empty)_ or `<abs-dir>` | Fetch | Run CLI → `Write` to `{dir}/{YYYY-MM-DD-HHMM}.md` (mkdir -p first). If no path in args, use `local_archive_dir` from `config.json`. |
| `recall` or `recall <abs-dir>` | Recall | `ls -1 {dir}/*.md \| tail -1` → `Read` it → output verbatim. Same path resolution as fetch. |

**Path resolution**:
1. If args include an absolute path, use it.
2. Otherwise, read `local_archive_dir` from this skill's `config.json`.
3. If neither is set, output an error and stop:
   ```
   Error: weather-pulse requires a directory. Pass one in args (e.g. `/weather-pulse /abs/path`) or set `local_archive_dir` in config.json.
   ```

Never silently guess a path from prior runs or conversation context.

## Fetch mode steps

1. Run: `Bash: /usr/bin/python3 {skill-dir}/pulse.py` (system Python — python.org Python may have broken SSL certs on macOS). Capture stdout.
2. Resolve the target directory per the rules above. Create it if missing.
3. Compute filename `{YYYY-MM-DD-HHMM}.md` from the local clock and write the report there.
4. Done. No reply, no notification, no rescheduling.

If the CLI exits non-zero: write a stub file with header `WEATHER PULSE FAILED — {timestamp} — {error}` so the gap is visible. Don't retry — the next cron run is the retry.

## Recall mode steps

1. Resolve the target directory per the rules above.
2. List `.md` files, lex-sort, take the last one (filename format `YYYY-MM-DD-HHMM.md` sorts correctly).
3. Output the file contents verbatim — no summary, no preamble. The calling agent will parse it.
4. If the latest report is **>8h old** (check timestamp in the report header), prepend one warning line:
   ```
   ⚠️ Latest report is {N}h old (from {timestamp}). Run /weather-pulse to refresh.
   ```
   Don't auto-refresh — that's a side-effect with cost. Let the caller decide.

## Examples

```
/weather-pulse                                   # fetch → uses local_archive_dir from config
/weather-pulse /home/me/weather-reports          # fetch → that folder
/weather-pulse recall                            # recall latest from configured folder
/weather-pulse recall /home/me/weather-reports   # recall latest from that folder
```

For cron, bake the path into the prompt or rely on `local_archive_dir`. Recall is for agents that want context but don't need to pay the cost of a fresh fetch.

## First-time setup

If you're using this skill for the first time:
1. Set your location: `python3 pulse.py --set-zip <your-zip>` (US zip codes only — the data source is the National Weather Service).
2. Set `local_archive_dir` in `config.json` to where you want reports stored, OR pass a path in args every time.
3. (Optional) Tune the thresholds in `config.json` — see README for what each section controls.

## Out of scope

- Sending notifications or messages. This skill only writes files.
- Locations outside the US. NWS doesn't cover them.
- Self-rescheduling. Cron / loop tooling owns the cadence.
