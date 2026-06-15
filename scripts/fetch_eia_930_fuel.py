#!/usr/bin/env python3
"""
fetch_eia_930_fuel.py — Fetch hourly generation by fuel type from EIA-930 API v2.

Usage:
    EIA_API_KEY=xxx python3 fetch_eia_930_fuel.py --start 2024-06-01 --end 2024-06-30 --ba CAL

Outputs:
    data/raw/eia930_fuel_CAL_2024-06.csv.gz
"""
import urllib.request, urllib.parse, json, sys, os, time, gzip, io
import pandas as pd
from datetime import datetime, timedelta

# ── Config ──────────────────────────────────────────────────────────────────
API_KEY=os.environ.get("EIA_API_KEY", "")
if not API_KEY:
    print("ERROR: Set EIA_API_KEY environment variable")
    sys.exit(1)

BASE_URL = "https://api.eia.gov/v2/electricity/rto/fuel-type-data/data/"
HEADERS = {"User-Agent": "DispatchabilityResearch/0.2"}

# EIA fuel type codes
FUEL_NAMES = {
    "COL": "Coal",
    "NG":  "Natural Gas",
    "NUC": "Nuclear",
    "OIL": "Petroleum",
    "OTH": "Other",
    "SUN": "Solar",
    "WAT": "Hydro",
    "WND": "Wind",
}


def fetch_day(ba: str, date_str: str) -> list[dict]:
    """Fetch one day of fuel-type generation for a balancing authority."""
    params = {
        "api_key": API_KEY,
        "frequency": "hourly",
        "data[0]": "value",
        "facets[respondent][]": ba,
        "start": f"{date_str}T00",
        "end":   f"{date_str}T23",
        "length": 500,
    }
    url = BASE_URL + "?" + urllib.parse.urlencode(params, doseq=True)
    req = urllib.request.Request(url, headers=HEADERS)
    
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
            return data.get("response", {}).get("data", [])
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = 5 * (attempt + 1)
                print(f"  Rate limited, waiting {wait}s...")
                time.sleep(wait)
            else:
                print(f"  HTTP {e.code}: {e.reason}")
                return []
        except Exception as e:
            print(f"  Error: {e}")
            return []
    print(f"  Failed after 3 retries for {date_str}")
    return []


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", default="2024-06-01")
    parser.add_argument("--end",   default="2024-06-30")
    parser.add_argument("--ba",    default="CAL", help="Balancing authority code (CAL=CAISO)")
    args = parser.parse_args()

    start_date = datetime.strptime(args.start, "%Y-%m-%d")
    end_date   = datetime.strptime(args.end, "%Y-%m-%d")
    
    all_rows = []
    current = start_date
    day_count = 0
    
    print(f"Fetching EIA-930 fuel-type data for {args.ba}")
    print(f"  Period: {args.start} to {args.end}")
    
    while current <= end_date:
        date_str = current.strftime("%Y-%m-%d")
        rows = fetch_day(args.ba, date_str)
        if rows:
            all_rows.extend(rows)
            day_count += 1
            if day_count % 5 == 0:
                print(f"  {date_str}: {len(rows)} records (total: {len(all_rows)})")
        else:
            print(f"  {date_str}: NO DATA")
        current += timedelta(days=1)
        time.sleep(0.3)  # be polite
    
    print(f"\nFetched {len(all_rows)} records over {day_count} days")
    
    # Convert to DataFrame
    df = pd.DataFrame(all_rows)
    
    # Clean
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df["period"] = pd.to_datetime(df["period"], format="%Y-%m-%dT%H")
    df = df.rename(columns={
        "respondent": "ba_code",
        "respondent-name": "ba_name",
        "fueltype": "fuel_code",
        "type-name": "fuel_name",
        "value": "generation_mwh",
        "value-units": "units",
    })
    
    # Map fuel codes to clean names
    df["fuel_name"] = df["fuel_code"].map(FUEL_NAMES).fillna(df["fuel_name"])
    
    # Sort
    df = df.sort_values(["period", "fuel_code"]).reset_index(drop=True)
    
    # Save
    year_month = start_date.strftime("%Y-%m")
    out_path = f"data/raw/eia930_fuel_{args.ba}_{year_month}.csv.gz"
    df.to_csv(out_path, index=False, compression="gzip")
    
    print(f"\nSaved {len(df)} rows to {out_path}")
    
    # Quick summary
    pivot = df.pivot_table(index="period", columns="fuel_name", values="generation_mwh", aggfunc="first")
    print(f"\nGeneration summary (MWh, monthly totals by fuel):")
    totals = pivot.sum().sort_values(ascending=False)
    for fuel, total in totals.items():
        pct = total / totals.sum() * 100
        print(f"  {fuel:15s}: {total:>10,.0f} MWh  ({pct:5.1f}%)")
    
    print(f"\n  TOTAL: {totals.sum():,.0f} MWh")


if __name__ == "__main__":
    main()
