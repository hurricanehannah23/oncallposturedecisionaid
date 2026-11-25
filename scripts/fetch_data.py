#!/usr/bin/env python3
"""Fetch every source the On-Call Posture Decision Aid reads and save it as JSON next to the page.

Run by the GitHub Actions workflow before each deploy:
    python scripts/fetch_data.py _site/data

Standard library only. A source that fails is left out; the page then calls that API live.
"""
import json
import os
import sys
import time
import urllib.request
from datetime import datetime, timezone

SITES = [
    {"id": "KSC", "lat": 28.5383, "lon": -80.6503},
    {"id": "CCSFS", "lat": 28.4884, "lon": -80.5778},
]
REPO = os.environ.get("GITHUB_REPOSITORY", "local")
# api.weather.gov asks every client to identify itself in the User-Agent.
UA = f"45ws-on-call-posture (github.com/{REPO})"


def get(url, tries=3):
    last = None
    for i in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/geo+json, application/json"})
            with urllib.request.urlopen(req, timeout=45) as r:
                return json.loads(r.read().decode("utf-8"))
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(3 * (i + 1))
    raise last


def main(out):
    os.makedirs(out, exist_ok=True)
    files, errors = {}, {}

    def save(name, fn):
        try:
            data = fn()
            with open(os.path.join(out, name), "w", encoding="utf-8") as f:
                json.dump(data, f, separators=(",", ":"))
            files[name] = True
            print(f"ok    {name}")
        except Exception as e:  # noqa: BLE001
            errors[name] = str(e)[:200]
            print(f"FAIL  {name}: {e}", file=sys.stderr)

    points = {}
    for s in SITES:
        try:
            points[s["id"]] = get(f"https://api.weather.gov/points/{s['lat']},{s['lon']}")["properties"]
        except Exception as e:  # noqa: BLE001
            errors[f"points_{s['id']}"] = str(e)[:200]

    for s in SITES:
        p = points.get(s["id"])
        if p:
            save(f"grid_{s['id']}.json", lambda p=p: get(p["forecastGridData"]))
        save(f"alerts_{s['id']}.json", lambda s=s: get(f"https://api.weather.gov/alerts/active?point={s['lat']},{s['lon']}"))
    if points.get("KSC"):
        save("forecast_KSC.json", lambda: get(points["KSC"]["forecast"]))

    for n in (1, 2, 3):
        save(f"spc_day{n}.json", lambda n=n: get(f"https://www.spc.noaa.gov/products/outlook/day{n}otlk_cat.lyr.geojson"))
    for n in (4, 5, 6, 7, 8):
        save(f"spc_day{n}.json", lambda n=n: get(f"https://www.spc.noaa.gov/products/exper/day4-8/day{n}prob.lyr.geojson"))

    for s in SITES:   # GFS winds at 262 ft (80 m) and 394 ft (120 m) for the Winds aloft row
        save(f"aloft_{s['id']}.json", lambda s=s: get(
            f"https://api.open-meteo.com/v1/gfs?latitude={s['lat']}&longitude={s['lon']}"
            "&hourly=wind_speed_10m,wind_gusts_10m,wind_speed_80m,wind_direction_80m,wind_speed_120m,wind_direction_120m"
            "&wind_speed_unit=kn&timezone=GMT&forecast_days=8"))

    save("nhc.json", lambda: get("https://www.nhc.noaa.gov/CurrentStorms.json"))

    def afd():
        lst = get("https://api.weather.gov/products/types/AFD/locations/MLB")
        first = (lst.get("@graph") or [None])[0]
        if not first:
            raise RuntimeError("no AFD listed")
        return get(first.get("@id") or f"https://api.weather.gov/products/{first['id']}")
    save("afd.json", afd)

    meta = {"fetched": datetime.now(timezone.utc).isoformat(timespec="seconds"), "files": files, "errors": errors}
    with open(os.path.join(out, "meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=1)
    print(f"{len(files)} saved, {len(errors)} failed")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "data")
