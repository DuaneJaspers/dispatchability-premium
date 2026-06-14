"""
fetch_caiso_dam_lmp.py — Fetch CAISO Day-Ahead Market LMPs.

Pulls hourly DAM Locational Marginal Prices (LMP) and all 5 components
(LMP, MCC, MCE, MCL, MGHG) for a set of representative trading-hub nodes
across a date range, with chunking to stay within CAISO's per-query window.

Source: CAISO OASIS public API (no authentication required).
  - Endpoint: https://oasis.caiso.com/oasisapi/SingleZip
  - Query:    PRC_LMP (PRC = price)
  - Market:   DAM (day-ahead market)
  - Version:  12
  - Format:   6 = CSV
  - Node IDs (representative trading-hub generation aggregate pricing nodes):
      TH_NP15_GEN-APND  — NP15 hub generation aggregate (PG&E territory)
      TH_SP15_GEN-APND  — SP15 hub generation aggregate (SCE territory)
      TH_ZP26_GEN-APND  — ZP26 hub generation aggregate (Fresno / central)
  - CAISO caps each query at ~7 days for DAM PRC_LMP; we chunk.

Output: data/raw/caiso_lmp_YYYY_MM.csv.gz
"""

import argparse
import io
import sys
import time
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import requests

CAISO_OASIS_URL = "https://oasis.caiso.com/oasisapi/SingleZip"
NODES = ["TH_NP15_GEN-APND", "TH_SP15_GEN-APND", "TH_ZP26_GEN-APND"]
DAYS_PER_CHUNK = 6  # safe under the ~7-day per-query cap
MAX_RETRIES = 3
RETRY_BACKOFF = 5  # seconds


def fetch_chunk(start: datetime, end: datetime) -> pd.DataFrame:
    """Fetch a single chunk of CAISO DAM LMPs and return the raw DataFrame."""
    url = (
        f"{CAISO_OASIS_URL}?resultformat=6&queryname=PRC_LMP&version=12"
        f"&startdatetime={start.strftime('%Y%m%dT%H:%M')}-0000"
        f"&enddatetime={end.strftime('%Y%m%dT%H:%M')}-0000"
        f"&market_run_id=DAM&node={','.join(NODES)}"
    )
    for attempt in range(MAX_RETRIES):
        try:
            r = requests.get(url, timeout=60, headers={"User-Agent": "dispatchability-premium-study/0.1 (research)"})
            r.raise_for_status()
            break
        except (requests.RequestException, requests.HTTPError) as e:
            if attempt < MAX_RETRIES - 1:
                print(f"  retry {attempt+1}/{MAX_RETRIES} after {RETRY_BACKOFF}s: {e}", file=sys.stderr)
                time.sleep(RETRY_BACKOFF * (attempt + 1))
            else:
                raise
    z = zipfile.ZipFile(io.BytesIO(r.content))
    with z.open(z.namelist()[0]) as f:
        df = pd.read_csv(f)
    return df


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--year-month", required=True, help="Year-month to fetch, e.g., 2024-06")
    parser.add_argument("--out-dir", default="data/raw", help="Output directory for the gzipped CSV")
    parser.add_argument("--start-day", type=int, default=1, help="First day of month (1-based)")
    parser.add_argument("--end-day", type=int, default=0, help="Last day of month (0 = last day of month)")
    args = parser.parse_args()

    year, month = map(int, args.year_month.split("-"))

    if args.end_day == 0:
        # Compute last day of month
        if month == 12:
            next_month = datetime(year + 1, 1, 1, tzinfo=timezone.utc)
        else:
            next_month = datetime(year, month + 1, 1, tzinfo=timezone.utc)
        last_day = (next_month - timedelta(days=1)).day
    else:
        last_day = args.end_day

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"caiso_lmp_{year:04d}_{month:02d}.csv.gz"

    print(f"Fetching CAISO DAM LMPs for {year:04d}-{month:02d}, days {args.start_day}–{last_day}")
    print(f"Nodes: {NODES}")
    print(f"Output: {out_path}")
    print()

    all_chunks = []
    day = args.start_day
    while day <= last_day:
        # Compute the end day of this chunk. We use end_day = day + DAYS_PER_CHUNK,
        # but cap it so we don't overshoot the month. The end *datetime* passed to
        # CAISO is (year, month, end_day+1) at 00:00 UTC (CAISO end is exclusive).
        end_day = min(day + DAYS_PER_CHUNK, last_day)
        days_in_chunk = end_day - day + 1
        chunk_start = datetime(year, month, day, 0, 0, tzinfo=timezone.utc)
        # End datetime is the day after end_day, at 00:00 UTC. If that would
        # overflow the month, we need to roll into the next month.
        if end_day == last_day:
            # Last chunk: end is first day of the following month, 00:00 UTC
            if month == 12:
                chunk_end = datetime(year + 1, 1, 1, 0, 0, tzinfo=timezone.utc)
            else:
                chunk_end = datetime(year, month + 1, 1, 0, 0, tzinfo=timezone.utc)
        else:
            chunk_end = datetime(year, month, end_day + 1, 0, 0, tzinfo=timezone.utc)
        print(f"  chunk: {chunk_start.date()} to {chunk_end.date() - timedelta(days=1)} ({days_in_chunk} days)")
        df = fetch_chunk(chunk_start, chunk_end)
        print(f"    rows: {len(df)}")
        all_chunks.append(df)
        day = end_day + 1
        time.sleep(5)  # polite; CAISO rate-limits aggressively (429s)

    combined = pd.concat(all_chunks, ignore_index=True)
    print(f"\nTotal rows: {len(combined)}")
    print(f"Date range: {combined['OPR_DT'].min()} to {combined['OPR_DT'].max()}")
    print(f"Nodes: {sorted(combined['NODE_ID'].unique().tolist())}")
    print(f"LMP types: {combined['LMP_TYPE'].value_counts().to_dict()}")

    # Save
    combined.to_csv(out_path, index=False, compression="gzip")
    print(f"\nSaved to {out_path} ({out_path.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
