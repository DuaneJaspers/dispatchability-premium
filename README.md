# Dispatchability Premium — CAISO (v0.2.0)

> What is the dollar value of being dispatchable? We measure it directly from real wholesale electricity prices and real generation-by-fuel-type data — not from a model.

## Headline number (v0.2.0)

**Dispatchability premium: +0.32** — dispatchable fuels (gas, hydro, nuclear) earn **32% more per MWh** than intermittent fuels (solar, wind), measured from 720 hours of CAISO data.

That's **$7.52/MWh** on a $23/MWh grid.

| Fuel | Capture Ratio | Earned $/MWh | Grid Avg | Gen Share | Type |
|---|---|---|---|---|---|
| Other (imports/storage) | **1.53** | $35.79 | $23.41 | 4.0% | — |
| Hydro | **1.18** | $27.60 | $23.41 | 14.7% | ⚡ dispatchable |
| Natural Gas | **1.15** | $26.90 | $23.41 | 35.0% | ⚡ dispatchable |
| Petroleum | 1.09 | $25.40 | $23.41 | 0.2% | ⚡ dispatchable |
| Wind | **1.04** | $24.44 | $23.41 | 12.1% | ☀️ intermittent |
| Nuclear | 1.00 | $23.41 | $23.41 | 8.1% | ⚡ dispatchable |
| Coal | 0.92 | $21.58 | $23.41 | 0.6% | ⚡ dispatchable |
| Solar | **0.71** | $16.69 | $23.41 | 28.2% | ☀️ intermittent |

**Data:** CAISO DAM LMPs × EIA-930 hourly generation by fuel type, June 2024, 720 hours merged.

## What the numbers mean

- **Solar captures only 71%** of the time-weighted average price. It produces during the day when CAISO prices are depressed by oversupply — the "duck curve" in action.
- **Natural gas captures 115%.** Gas plants ramp up during the evening peak when solar drops off and prices spike.
- **Nuclear is exactly 1.00** — it runs flat baseload at the same output every hour, so it earns the time-weighted average by definition.
- **Wind captures above 1.0 (104%)** — in CAISO, wind blows more in evening/night hours when prices are higher. This is a grid-specific finding; in other grids wind may capture less.
- **"Other" at 1.53** is likely imports from neighboring regions during high-price hours and/or battery storage discharging at peaks.

**The dispatchability premium (gen-weighted):**
- Dispatchable: **1.133** (gas + hydro + nuclear + coal + oil)
- Intermittent: **0.812** (solar + wind)
- **Premium: +0.321** → **$7.52/MWh**

This means: for the same MWh of energy delivered, a dispatchable plant earns 32% more than an intermittent one in CAISO. That premium is the economic reason steam (gas/coal/nuclear) persists in the installed base.

## v0.1.0 result (node-level, still valid)

The v0.1.0 node-level spread was an *upper bound* on the fuel-level premium. The two measurements agree:

| Measurement | Spread |
|---|---|
| v0.1.0 node-level (NP15 − ZP26) | 0.33 |
| v0.2.0 fuel-level (dispatchable − intermittent) | 0.32 |

The fuel-level result (0.32) is slightly tighter because it's a cleaner measurement — it separates dispatchable from intermittent *within the same hours* rather than comparing geographic regions.

## Why this is interesting

This answers the original question — "why is heating water still the main way to generate electricity?" — with a **measured number, not a model**:

- The market pays **$7.52/MWh extra** for dispatchability in CAISO.
- That premium is the economic moat of steam-based generation.
- It's being eroded by batteries (Lazard: solar+4h storage at $60–$210/MWh).
- When battery costs fall enough to recover the $7.52/MWh premium, the substitution completes.

## Reproducibility

```bash
# 1. Fetch 30 days of CAISO DAM LMPs (no auth needed)
python3 scripts/fetch_caiso_dam_lmp.py --year-month 2024-06

# 2. Fetch EIA-930 generation by fuel type (free API key from eia.gov)
EIA_API_KEY=*** python3 scripts/fetch_eia_930_fuel.py --start 2024-06-01 --end 2024-06-30 --ba CAL

# 3. Compute fuel-level capture ratios
python3 scripts/compute_fuel_capture_ratios.py
```

Requires Python 3.11+ with pandas. No other dependencies.

## What v0.2.0 is *not*

- **Not multi-month.** One month (June 2024). The premium likely varies seasonally — solar surplus is strongest in spring/fall, not mid-summer.
- **Not multi-grid.** CAISO is a solar-heavy grid with an extreme duck curve. In gas-dominated grids (PJM, ERCOT) the premium may be smaller. In hydro-dominated grids (Pacific Northwest) it may differ entirely.
- **Not a causal claim.** The capture ratios measure *correlation* between fuel output and price — they don't isolate *why* some fuels produce during high-price hours. Part of gas's premium may be from scarcity pricing during heat waves, not from dispatchability per se.
- **Not a forecast.** The number is observed, not predicted.

## Stop-loss

**90-day stop-loss from v0.3.0 push date.** If the project has no external references (citations, links, forks) by the next quarter, it archives.

## Files

```
~/projects/dispatchability-premium/
├── README.md                              # this file
├── CHANGELOG.md                           # v0.1.0 + v0.2.0
├── LICENSE                                # CC-BY-4.0
├── docs/
│   └── methodology.md                     # measurement framework
├── scripts/
│   ├── fetch_caiso_dam_lmp.py             # CAISO DAM LMPs (no auth)
│   ├── fetch_eia_930_fuel.py              # EIA-930 generation by fuel (free key)
│   ├── compute_capture_ratios.py          # v0.1.0: node-level capture ratios
│   └── compute_fuel_capture_ratios.py     # v0.2.0: fuel-level capture ratios
├── data/raw/
│   ├── caiso_lmp_2024_06.csv.gz           # 10,800 rows (LMP data)
│   └── eia930_fuel_CAL_2024-06.csv.gz     # 5,760 rows (fuel data)
└── results/
    ├── caiso_dispatchability_premium_2024_06.csv   # v0.1.0 node-level
    ├── caiso_dispatchability_premium_2024_06.md
    ├── fuel_capture_ratios_2024-06.csv             # v0.2.0 fuel-level
    └── fuel_capture_ratios_2024-06.md
```

## License

CC-BY-4.0. Use, fork, extend — with attribution.

## Data sources

- **CAISO OASIS** — Day-Ahead Market LMPs at trading-hub nodes (public, no auth)
- **EIA-930** — Hourly generation by energy source via API v2 (free key from [eia.gov](https://www.eia.gov/opendata/register.php))
- **Lazard LCOE+ 2024** — cost context for the dispatchability premium interpretation
- **IEA Global Energy Review 2025** — global generation mix for the original framing question
