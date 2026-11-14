"""BLOOM: fetch real NASA POWER IMERG point rainfall for Jericho, 2005-2024.

Run this script from the BLOOM repository with:
  python scripts/fetch_nasa_power.py

IMPORTANT: A point time series is not the same as GPM estimates aggregated over
area_a and area_b. This script writes a separate supporting dataset and does
not overwrite data/rainfall_annual.csv (the polygon-based contract file).
"""

import csv
import json
import math
from calendar import isleap
from collections import defaultdict
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import urlopen

URL = "https://power.larc.nasa.gov/api/temporal/daily/point"
PARAMS = {
    "parameters": "IMERG_PRECTOT",
    "community": "AG",
    "latitude": "31.86",       # Approximate Jericho city point, NOT a study polygon
    "longitude": "35.45",
    "start": "20050101",
    "end": "20241231",
    "time-standard": "UTC",   # Required for IMERG in NASA POWER
    "format": "JSON",
}


def main():
    api_url = URL + "?" + urlencode(PARAMS)
    print("Requesting NASA POWER IMERG daily rainfall...")
    try:
        with urlopen(api_url, timeout=180) as response:
            payload = json.load(response)
    except (HTTPError, URLError, TimeoutError, ValueError) as exc:
        raise SystemExit(f"NASA POWER request failed: {exc}") from exc

    series = payload.get("properties", {}).get("parameter", {}).get("IMERG_PRECTOT")
    if not isinstance(series, dict):
        raise SystemExit(
            "NASA POWER did not return IMERG_PRECTOT. "
            f"API messages: {payload.get('messages', [])}"
        )

    totals = defaultdict(float)
    counts = defaultdict(int)
    for day, raw_value in series.items():
        if not (isinstance(day, str) and len(day) == 8 and day.isdigit()):
            continue
        year = int(day[:4])
        if year < 2005 or year > 2024:
            continue
        try:
            value = float(raw_value)
        except (TypeError, ValueError):
            continue
        if not math.isfinite(value) or value == -999 or value < 0:
            continue
        totals[year] += value    # NASA IMERG_PRECTOT is daily accumulated mm
        counts[year] += 1

    root = Path(__file__).resolve().parents[1]
    output = root / "data" / "nasa_power_jericho_point_rainfall.csv"
    output.parent.mkdir(parents=True, exist_ok=True)
    complete_years = 0

    with output.open("w", newline="", encoding="utf-8") as fp:
        writer = csv.DictWriter(fp, fieldnames=[
            "year", "rainfall_mm", "valid_days", "expected_days", "status"
        ])
        writer.writeheader()
        for year in range(2005, 2025):
            expected = 366 if isleap(year) else 365
            complete = counts[year] == expected
            if complete:
                complete_years += 1
            writer.writerow({
                "year": year,
                "rainfall_mm": round(totals[year], 2) if complete else "",
                "valid_days": counts[year],
                "expected_days": expected,
                "status": "complete" if complete else "incomplete",
            })

    print(f"Saved: {output}")
    print(f"Complete years: {complete_years}/20")
    if complete_years == 0:
        print("WARNING: No complete years. Check service availability and API output.")
    print("Source: NASA POWER / GPM IMERG, daily point data, UTC, mm/day accumulated as mm.")
    print("Do NOT rename this file to rainfall_annual.csv: it is not polygon-aggregated.")


if __name__ == "__main__":
    main()
