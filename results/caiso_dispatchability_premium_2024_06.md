# CAISO Dispatchability Premium — Summary

**Window:** 2024-05-31 to 2024-06-30
**Market:** CAISO Day-Ahead Market (DAM)
**Hours in window:** 720
**Nodes:** ['TH_NP15_GEN-APND', 'TH_SP15_GEN-APND', 'TH_ZP26_GEN-APND']

## Headline

- **Capture-ratio spread:** 0.3336 (max − min across nodes)
- **Highest capture ratio:** `TH_NP15_GEN-APND` = 1.1985
- **Lowest capture ratio:** `TH_ZP26_GEN-APND` = 0.8649

## Per-node statistics (capture ratio = node LMP / grid-average LMP)

| Node | mean | std | min | max | median |
|-----|------|-----|-----|-----|--------|
| `TH_NP15_GEN-APND` | 1.1985 | 4.0471 | -23.5526 | 97.4857 | 0.9922 |
| `TH_SP15_GEN-APND` | 0.9366 | 1.6311 | -39.2231 | 7.6757 | 1.0093 |
| `TH_ZP26_GEN-APND` | 0.8649 | 2.4341 | -55.2626 | 18.8769 | 0.9973 |

## What this means (and doesn't)

A capture ratio of 1.0 means the node captures exactly the grid-average price.
A capture ratio > 1.0 means the node tends to be dispatched in higher-price hours
(because the marginal unit in those hours is more expensive).
A capture ratio < 1.0 means the node tends to be dispatched in lower-price hours
(e.g., when solar is abundant).

**Caveat (v0.1.0):** the three CAISO trading-hub nodes are *aggregates* of
many generators (solar + gas + nuclear + imports). We have *not* yet split
by fuel type. The capture-ratio spread is therefore an *upper bound* on
the true dispatchability premium (between fuel types). v0.2.0 will use
EIA-930 hourly generation-by-fuel-type to disambiguate.

## Reproducibility

- **Data source:** CAISO OASIS PRC_LMP (DAM, version 12, CSV format 6)
- **Pipeline:** `scripts/fetch_caiso_dam_lmp.py` → `scripts/compute_capture_ratios.py`
- **Methodology:** `docs/methodology.md`
- **Reproducibility:** all data is public, all code is in this repository
