---
name: changelog
description: "Changelog for the dispatchability-premium project."
---

# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.1.0] - 2026-06-14

### Added
- `docs/methodology.md` — full definition of the dispatchability premium measurement
- `scripts/fetch_caiso_dam_lmp.py` — CAISO DAM LMP fetcher (no auth, 6-day chunks, polite)
- `scripts/compute_capture_ratios.py` — capture-ratio and spread computation
- `data/raw/caiso_lmp_2024_06.csv.gz` — 10,800 rows × 5 LMP types × 3 nodes × 30 days
- `results/caiso_dispatchability_premium_2024_06.csv` and `.md` — headline numbers

### Verified findings
- **Capture-ratio spread (NP15 − ZP26): 0.3336** for CAISO DAM, June 2024.
- **NP15 mean capture ratio: 1.20** (PG&E territory, more gas baseload).
- **ZP26 mean capture ratio: 0.86** (Fresno, more solar).
- **SP15 mean capture ratio: 0.94** (SCE, mixed).
- 720 hours of clean DAM data successfully retrieved from CAISO OASIS SingleZip API.

### Stop-loss
- ≤ v0.1.0 → kill if no external traction in 90 days (by 2026-09-14).
- > v0.1.0 → expand to multi-month, multi-fuel, multi-grid.

### Acknowledged prior work (not duplicated)
- **fneum/price-formation** (2026) — theoretical price formation in 100% VRE systems; empirical measurements, not theoretical models.
- **LukasFrankenQ/GBPower** (2024) — full GB market model using PyPSA/Elexon; *unit commitment* model, not the same as our price-formation measurement.
- **c-leblanc/EOLES-Dispatch** — French dispatch model with HiGHS solver (free, not Gurobi); closest existing tool, but covers France not CAISO.
- **RMI/dispatch** (2025) — simplified dispatch; not price-formation focus.
- **Hirth (2013)** — original value-factor framework. **SSRN 5078970** (2024) — recent value-factor estimation. **Ofgem / Imperial (2018)** — UK baseload value study.

### What this project is the *first* to do
- Compute the **empirical capture-ratio spread** for a major US grid (CAISO) using only the public OASIS API.
- Distribute the pipeline as a single-author, **zero-funds reproducible artifact** (free data + free Python venv + cc-by-licensed code).
- Frame the number as the **value of dispatchability** that coal/gas plants implicitly receive and renewables implicitly pay for — i.e., the answer to the user's original question.
