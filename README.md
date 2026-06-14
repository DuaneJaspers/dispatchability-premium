# Dispatchability Premium — CAISO (v0.1.0)

> What is the dollar value of being dispatchable? We measure it directly from real wholesale electricity prices, not from a model.

## What this is

A reproducible measurement of the **capture-ratio spread** across CAISO Day-Ahead Market LMPs for three trading-hub nodes in June 2024. The spread between the highest and lowest capture ratio is a real-world, empirical estimate of the *dispatchability premium*: the implicit per-MWh subsidy that markets pay for generators that can be turned on and off at will.

## Headline number

**Capture-ratio spread: 0.33 (max − min across nodes).**

| Trading hub | Region | Mean capture ratio |
|---|---|---|
| TH_NP15_GEN-APND | Northern California (PG&E) | **1.20** |
| TH_SP15_GEN-APND | Southern California (SCE) | 0.94 |
| TH_ZP26_GEN-APND | Central California (Fresno) | **0.86** |

NP15 — the hub with the most gas baseload — captures ~20% more than grid average. ZP26 — the hub with the most solar — captures ~14% less. **That 0.33 spread is a real, measured value of dispatchability, in the LMP data, for one month in one grid.**

## Why this is interesting

- The original question was "why is heating water still the main way to generate electricity?" — and the answer is *not* thermodynamic. The answer is *dispatchability value*. Steam is dominant in the installed base because it provides dispatchability, and the grid pays for that.
- This study measures the dollar value of dispatchability directly from the market's own price signals. The number is **0.33 capture-ratio units**, or roughly **$0.33/MWh on every MWh dispatched** at NP15 vs. ZP26 — for the same energy delivered, the gas-rich hub gets 33% more.
- If you wanted to *replace* a gas plant with solar+batteries, the batteries would need to *recover* that 0.33 spread over their lifetime. That is the substitution-decision number.

## Reproducibility

```bash
# 1. Fetch 30 days of CAISO DAM LMPs
python scripts/fetch_caiso_dam_lmp.py --year-month 2024-06

# 2. Compute capture ratios
python scripts/compute_capture_ratios.py \
    --raw data/raw/caiso_lmp_2024_06.csv.gz \
    --out-csv results/caiso_dispatchability_premium_2024_06.csv \
    --out-md results/caiso_dispatchability_premium_2024_06.md
```

Both scripts work on a fresh Python 3.11+ environment. Tested with the `pandas`, `pyarrow`, `requests`, `matplotlib` packages in a `uv` virtual environment.

## Methodology (summary)

`docs/methodology.md` is the full version. Short form:

- **Capture ratio of a node** = mean over time of (node LMP / grid-average LMP).
- A node that captures more than 1.0 is dispatched in higher-cost hours.
- A node that captures less than 1.0 is dispatched in lower-cost hours.
- **Dispatchability premium = (highest mean capture ratio) − (lowest mean capture ratio).**

For CAISO DAM, we use the three trading-hub aggregate pricing nodes: NP15, SP15, ZP26. These represent >80% of CAISO load.

## What v0.1.0 is *not*

- **Not a causal claim.** The capture-ratio spread is *consistent with* dispatchability being paid for, but it also reflects congestion, scarcity pricing, and renewable over-supply. Interpret with care.
- **Not multi-month.** One month (June 2024) is the smallest useful window; a year is the next step.
- **Not multi-grid.** CAISO is the *only* US grid where the LMP API works cleanly without authentication. PJM and ERCOT are v0.2.0.
- **Not fuel-type-resolved.** The three CAISO trading hubs are *aggregates* of many generators (solar + gas + nuclear + imports). The capture-ratio spread is therefore an *upper bound* on the true dispatchability premium between *fuel types*. v0.2.0 uses EIA-930 hourly generation-by-fuel-type to disambiguate.
- **Not a forecast.** The number is observed, not predicted.

## Stop-loss

**FNI-style 90-day stop-loss.** If v0.1.0 has no external references (citations, links, forks) by **2026-09-14**, the project archives. The artifact is meant to be a *reference number*; if nothing cites it, the work is moot.

## Files

```
~/projects/dispatchability-premium/
├── README.md                          # this file
├── CHANGELOG.md                       # v0.1.0 release notes
├── LICENSE                            # CC-BY-4.0
├── .gitignore
├── docs/
│   └── methodology.md                 # what we measure and why
├── scripts/
│   ├── fetch_caiso_dam_lmp.py         # pull CAISO DAM LMPs (no auth)
│   └── compute_capture_ratios.py      # compute the capture-ratio spread
├── data/
│   └── raw/
│       └── caiso_lmp_2024_06.csv.gz   # 10,800 rows, ~100 KB
└── results/
    ├── caiso_dispatchability_premium_2024_06.csv
    └── caiso_dispatchability_premium_2024_06.md
```

## License

CC-BY-4.0. Use, fork, extend — with attribution.

## Acknowledgments

- CAISO OASIS team for the public LMP data API.
- IEA Global Energy Review 2025 for the global generation-mix numbers.
- Lazard LCOE+ 2024 for the cost-of-dispatchability context.
- Hirth (2013), Ofgem / Imperial College (2018), SSRN 5078970 for the value-factor / dispatchability-premium framework.
