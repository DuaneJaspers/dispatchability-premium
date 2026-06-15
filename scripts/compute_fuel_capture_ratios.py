#!/usr/bin/env python3
"""
compute_fuel_capture_ratios.py — v0.2.0

Joins EIA-930 fuel-type generation with CAISO DAM LMPs
to compute capture ratios BY FUEL TYPE.

The dispatchability premium = difference in capture ratios
between dispatchable (gas, nuclear, hydro) and intermittent
(solar, wind) fuels.

Usage:
    python3 compute_fuel_capture_ratios.py
"""
import pandas as pd
import numpy as np
from pathlib import Path

# ── Config ──────────────────────────────────────────────────────────────────
LMP_FILE = "data/raw/caiso_lmp_2024_06.csv.gz"
FUEL_FILE = "data/raw/eia930_fuel_CAL_2024-06.csv.gz"
OUT_DIR = Path("results")
OUT_DIR.mkdir(exist_ok=True)

# ── Load LMP data ───────────────────────────────────────────────────────────
print("=== Loading data ===")
lmp_df = pd.read_csv(LMP_FILE, compression="gzip")
print(f"LMP data: {len(lmp_df)} rows")
print(f"Columns: {list(lmp_df.columns)}")
print(f"Sample:\n{lmp_df.head(3)}")
print()

# ── Load fuel data ──────────────────────────────────────────────────────────
fuel_df = pd.read_csv(FUEL_FILE, compression="gzip")
print(f"Fuel data: {len(fuel_df)} rows")
print(f"Columns: {list(fuel_df.columns)}")
print(f"Sample:\n{fuel_df.head(3)}")
print()

# ── Parse timestamps ────────────────────────────────────────────────────────
# CAISO LMP: check the timestamp format
print("=== Timestamp inspection ===")
print(f"LMP timestamp sample: {lmp_df.iloc[0]}")
# The CAISO data has 'INTERVALSTARTTIME_GMT' and 'INTERVALENDTIME_GMT'
# EIA data has 'period' in local-ish time

# Parse LMP timestamps
lmp_df["start_gmt"] = pd.to_datetime(lmp_df["INTERVALSTARTTIME_GMT"], utc=True)
lmp_df["end_gmt"] = pd.to_datetime(lmp_df["INTERVALENDTIME_GMT"], utc=True)
lmp_df["hour_gmt"] = lmp_df["start_gmt"].dt.floor("h")

# Parse EIA timestamps  
fuel_df["period"] = pd.to_datetime(fuel_df["period"])
# EIA-930 uses the local time of the balancing authority
# For CAL (CAISO), that's Pacific Time
# But the API might return it without timezone info
# Let's check: does solar peak at midday?
print("\n=== Solar generation by hour (timezone check) ===")
solar = fuel_df[fuel_df["fuel_code"] == "SUN"]
solar_by_hour = solar.groupby(solar["period"].dt.hour)["generation_mwh"].mean()
print("Hour: Solar MWh")
for hr, val in solar_by_hour.items():
    bar = "█" * int(val / max(solar_by_hour) * 30) if max(solar_by_hour) > 0 else ""
    print(f"  {hr:2d}h: {val:8,.0f}  {bar}")

# If solar peaks at 12-14h, the EIA timestamps are in local time (Pacific) ✓
# If solar peaks at 19-21h, the timestamps are in UTC and need conversion

solar_peak_hour = solar_by_hour.idxmax()
print(f"\nSolar peak hour: {solar_peak_hour}h")

if 10 <= solar_peak_hour <= 15:
    print("→ EIA timestamps appear to be in LOCAL TIME (Pacific) ✓")
    tz_note = "EIA-930 timestamps are local (Pacific). No conversion needed."
    fuel_df["hour_gmt"] = fuel_df["period"].dt.tz_localize("America/Los_Angeles").dt.tz_convert("UTC").dt.floor("h")
elif 18 <= solar_peak_hour <= 22:
    print("→ EIA timestamps appear to be in UTC. Converting to local...")
    tz_note = "EIA-930 timestamps were UTC; converted to local for alignment."
    fuel_df["hour_local"] = fuel_df["period"].dt.tz_localize("UTC").dt.tz_convert("America/Los_Angeles")
    fuel_df["hour_gmt"] = fuel_df["period"].dt.tz_localize("UTC").dt.floor("h")
else:
    print(f"→ Solar peak at {solar_peak_hour}h — ambiguous timezone. Treating as UTC.")
    tz_note = "EIA-930 timezone ambiguous; treated as UTC."
    fuel_df["hour_gmt"] = fuel_df["period"].dt.tz_localize("UTC").dt.floor("h")

# ── Pivot fuel data: hours × fuel types ─────────────────────────────────────
print("\n=== Joining LMP × Fuel ===")
fuel_pivot = fuel_df.pivot_table(
    index="hour_gmt", 
    columns="fuel_name", 
    values="generation_mwh", 
    aggfunc="first"
)
print(f"Fuel pivot: {fuel_pivot.shape[0]} hours × {fuel_pivot.shape[1]} fuels")

# Use NP15 LMP as representative price (or average across nodes)
lmp_np15 = lmp_df[lmp_df["NODE"] == "TH_NP15_GEN-APND"].copy()
lmp_np15 = lmp_np15[lmp_np15["LMP_TYPE"] == "LMP"]
lmp_np15 = lmp_np15[["hour_gmt", "MW"]].rename(columns={"MW": "lmp"})
lmp_np15["lmp"] = pd.to_numeric(lmp_np15["lmp"], errors="coerce")

# Also get SP15 and ZP26 for comparison
for node in ["TH_SP15_GEN-APND", "TH_ZP26_GEN-APND"]:
    node_df = lmp_df[lmp_df["NODE"] == node].copy()
    node_df = node_df[node_df["LMP_TYPE"] == "LMP"]
    short = node.split("_")[1]
    lmp_np15[f"lmp_{short}"] = pd.to_numeric(node_df.set_index("hour_gmt")["MW"], errors="coerce")

# Average LMP across all 3 nodes
all_lmps = lmp_df[lmp_df["LMP_TYPE"] == "LMP"].copy()
all_lmps["MW"] = pd.to_numeric(all_lmps["MW"], errors="coerce")
avg_lmp = all_lmps.groupby("hour_gmt")["MW"].mean().rename("lmp_avg")

print(f"LMP (NP15): {len(lmp_np15)} hours")
print(f"LMP (avg):  {len(avg_lmp)} hours")

# ── Join on hour_gmt ────────────────────────────────────────────────────────
merged = fuel_pivot.join(avg_lmp, how="inner")
print(f"Merged: {len(merged)} hours with both fuel + LMP data")

# ── Compute capture ratios by fuel type ─────────────────────────────────────
print("\n=== CAPTURE RATIOS BY FUEL TYPE ===")
print("Capture ratio = (generation-weighted avg price) / (time-weighted avg price)")
print("  > 1.0 → fuel produces more during high-price hours (dispatchable advantage)")
print("  < 1.0 → fuel produces more during low-price hours (intermittent penalty)")
print()

time_avg_price = merged["lmp_avg"].mean()
print(f"Time-weighted average price (all hours): ${time_avg_price:.2f}/MWh")
print()

results = []
for fuel in sorted(merged.columns.drop("lmp_avg")):
    gen = merged[fuel]
    mask = gen.notna() & (gen > 0)
    if mask.sum() < 24:
        continue
    
    gen_valid = gen[mask]
    prices_during_gen = merged.loc[mask, "lmp_avg"]
    
    # Revenue-weighted average price (what this fuel actually earns)
    revenue = (gen_valid * prices_during_gen).sum()
    total_gen = gen_valid.sum()
    rev_weighted_price = revenue / total_gen if total_gen > 0 else 0
    
    # Capture ratio
    capture = rev_weighted_price / time_avg_price if time_avg_price > 0 else 0
    
    # Additional stats
    gen_share = total_gen / merged.drop(columns=["lmp_avg"]).sum().sum() * 100
    capacity_factor = mask.sum() / len(merged) * 100
    avg_gen_when_on = gen_valid.mean()
    avg_price_when_on = prices_during_gen.mean()
    
    results.append({
        "fuel": fuel,
        "capture_ratio": capture,
        "rev_weighted_price": rev_weighted_price,
        "time_weighted_price": time_avg_price,
        "generation_mwh": total_gen,
        "gen_share_pct": gen_share,
        "capacity_factor_pct": capacity_factor,
        "avg_gen_mw": avg_gen_when_on,
        "avg_price_when_on": avg_price_when_on,
    })

results_df = pd.DataFrame(results).sort_values("capture_ratio", ascending=False)

# Print results table
print(f"{'Fuel':<15s} {'Capture':>8s} {'Earned':>10s} {'Grid Avg':>10s} {'Share':>7s} {'CF':>6s}")
print(f"{'':_<60s}")
for _, row in results_df.iterrows():
    marker = ""
    if row["fuel"] in ["Natural Gas", "Nuclear", "Hydro", "Coal", "Petroleum"]:
        marker = " ⚡dispatchable"
    elif row["fuel"] in ["Solar", "Wind"]:
        marker = " ☀️intermittent"
    print(f"{row['fuel']:<15s} {row['capture_ratio']:>8.3f} ${row['rev_weighted_price']:>8.2f} ${row['time_weighted_price']:>8.2f} {row['gen_share_pct']:>6.1f}% {row['capacity_factor_pct']:>5.1f}%{marker}")

# ── The dispatchability premium ─────────────────────────────────────────────
dispatchable_fuels = ["Natural Gas", "Nuclear", "Hydro", "Coal", "Petroleum"]
intermittent_fuels = ["Solar", "Wind"]

disp_capture = results_df[results_df["fuel"].isin(dispatchable_fuels)]
inter_capture = results_df[results_df["fuel"].isin(intermittent_fuels)]

disp_gen_weighted = (disp_capture["capture_ratio"] * disp_capture["generation_mwh"]).sum() / disp_capture["generation_mwh"].sum()
inter_gen_weighted = (inter_capture["capture_ratio"] * inter_capture["generation_mwh"]).sum() / inter_capture["generation_mwh"].sum()

premium = disp_gen_weighted - inter_gen_weighted

print(f"\n{'='*60}")
print(f"THE DISPATCHABILITY PREMIUM (CAISO, June 2024)")
print(f"{'='*60}")
print(f"Dispatchable fuels (gen-weighted):  {disp_gen_weighted:.4f}")
print(f"Intermittent fuels (gen-weighted):  {inter_gen_weighted:.4f}")
print(f"PREMIUM:                            {premium:+.4f}")
print(f"  → Dispatchable earns {premium*100:.1f}% more per MWh than intermittent")
print(f"  → On a ${time_avg_price:.0f}/MWh grid: ${time_avg_price * premium:.2f}/MWh extra")

# ── Save results ────────────────────────────────────────────────────────────
out_csv = OUT_DIR / "fuel_capture_ratios_2024-06.csv"
results_df.to_csv(out_csv, index=False)
print(f"\nSaved: {out_csv}")

# Save markdown report
md_lines = [
    f"# Fuel-Type Capture Ratios — CAISO, June 2024",
    f"",
    f"**Timezone note:** {tz_note}",
    f"**Data sources:** CAISO OASIS (DAM LMPs), EIA-930 (hourly generation by fuel)",
    f"**Merged hours:** {len(merged)}",
    f"**Time-weighted average price:** ${time_avg_price:.2f}/MWh",
    f"",
    f"| Fuel | Capture Ratio | Earned $/MWh | Grid Avg $/MWh | Gen Share | Capacity Factor |",
    f"|---|---|---|---|---|---|",
]
for _, row in results_df.iterrows():
    md_lines.append(f"| {row['fuel']} | {row['capture_ratio']:.4f} | ${row['rev_weighted_price']:.2f} | ${row['time_weighted_price']:.2f} | {row['gen_share_pct']:.1f}% | {row['capacity_factor_pct']:.1f}% |")

md_lines.extend([
    f"",
    f"## Dispatchability Premium",
    f"",
    f"| Category | Gen-weighted capture ratio |",
    f"|---|---|",
    f"| Dispatchable (gas, nuclear, hydro, coal, oil) | {disp_gen_weighted:.4f} |",
    f"| Intermittent (solar, wind) | {inter_gen_weighted:.4f} |",
    f"| **Premium** | **{premium:+.4f}** |",
    f"",
    f"On a ${time_avg_price:.0f}/MWh grid, the dispatchability premium is **${time_avg_price * premium:.2f}/MWh**.",
])

out_md = OUT_DIR / "fuel_capture_ratios_2024-06.md"
out_md.write_text("\n".join(md_lines))
print(f"Saved: {out_md}")
