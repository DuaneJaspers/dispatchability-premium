---
name: methodology
description: "The measurement framework. Defines what 'dispatchability premium' is, how to compute it, and what its known limitations are. Read this before the rest of the project."
---

# Methodology — What we are measuring and how

## The question

**"Why is heating water (the Rankine cycle) still the main way to generate electricity?"** is a *misframed* question. Steam is the **installed base** (35% of global generation in 2024 per IEA), not the **new-build winner** (renewables + nuclear > coal by early 2025 per IEA forecasts). The real question is:

> **What is the dollar value per MWh of the *dispatchability* that steam plants provide, and how fast is that value falling?**

That is the question the **dispatchability premium** answers. The premium is the gap between (a) the LMP a dispatchable generator actually receives in a competitive market and (b) the *levelized* LMP a non-dispatchable generator (variable renewable) actually receives, *for the same energy delivered*. If variable renewables capture less than 100% of the load-weighted average price, they implicitly *pay* for the lack of dispatchability; if a dispatchable generator captures more than 100%, it is *paid* for the dispatchability it provides. The gap between the two capture rates is the premium.

## The operational definition

For a chosen grid and a chosen window:

- **`LMP_dispatchable(t, n)`** = the Locational Marginal Price at a *dispatchable-unit* node n at time t.
- **`LMP_average(t)`** = the load-weighted average LMP across the grid at time t.
- **`LMP_renewable(t, n)`** = the LMP at a *variable-renewable* node n at time t (wind or solar). In markets where renewables are price-takers with no congestion, this equals the system LMP.

Three derived quantities (computed over the window W):

- **`capture_ratio_dispatchable` = mean_n( mean_t[ LMP_dispatchable(t,n) / LMP_average(t) ] )`** — fraction of the average price that a representative dispatchable unit captures.
- **`capture_ratio_renewable` = mean_n( mean_t[ LMP_renewable(t,n) / LMP_average(t) ] )`** — fraction for a representative variable-renewable unit.
- **`dispatchability_premium ($/MWh) = capture_ratio_dispatchable - capture_ratio_renewable`** — the *per-MWh premium* of being dispatchable.

A *positive* premium means dispatchable units are paid more per MWh delivered. A premium of 0.20 means $0.20/MWh on every MWh for the privilege of being dispatchable. This is the **Value Factor** in the Hirth (2013) framework, computed *empirically from real LMP data* rather than from a model.

## Why this is a useful measurement

- The premium is *observable in real data*, not estimated by a model.
- It captures the **grid-integration value** that the engineering literature is currently debating.
- It is the missing number that the dispatchability-replacement question reduces to: **at what premium does the substitution happen?**
- A widely cited, open, computed number across multiple grids is the kind of artifact the field orients around.

## The data we use

**Primary: CAISO Day-Ahead Market LMPs** (since 2014).

- **Source:** CAISO OASIS public API (no authentication, no rate limit, CSV).
- **Nodes chosen (representative):**
  - **TH_NP15_GEN-APND** — Northern California hub generation (PG&E territory, solar + gas + imports)
  - **TH_SP15_GEN-APND** — Southern California hub generation (SCE territory, solar + gas)
  - **TH_ZP26_GEN-APND** — Central California / Fresno (solar + gas)
  - The three SP15/NP15/ZP26 trading hubs represent >80% of CAISO load
- **LMP types pulled (all 5 components):**
  - LMP — total locational marginal price ($/MWh)
  - MCC — marginal congestion component
  - MCE — marginal energy component
  - MCL — marginal loss component
  - MGHG — marginal greenhouse-gas component (CAISO-specific carbon adder)
- **Granularity:** hourly intervals, day-by-day download (CAISO caps each query at ~7-day windows for DAM; 30 days for some queries).
- **Time window for v0.1.0:** one sample month (June 2024) to validate the pipeline end-to-end. **The v0.2.0 expansion to 3+ years is the next step after pipeline is verified.**

**Why CAISO first:** the only one of the three primary US grids where (a) the public LMP API works *without* an API key, (b) hourly resolution is real, and (c) all five LMP components are available, in a format I could verify in this session. PJM requires Data Miner 2 registration for full LMP feeds. ERCOT requires a different authentication pattern. CAISO works today. **The methodology transfers; the priority is what works without funds first.**

## What the pipeline produces

For the chosen window:

- **`data/raw/caiso_lmp_YYYY_MM.csv.gz`** — raw LMPs by node × hour × component.
- **`data/processed/caiso_capture_ratios_YYYY_MM.csv`** — capture ratios per node per hour.
- **`results/caiso_dispatchability_premium_YYYY_MM.csv`** — the headline number(s): capture ratio per node, per LMP component, with summary statistics.
- **`results/caiso_dispatchability_premium_YYYY_MM.md`** — a one-page human-readable write-up.

## What the headline output is *not*

- **Not** a causal claim. A *positive* premium is *consistent with* dispatchability being paid for, but the premium also reflects congestion, scarcity pricing, and the renewable over-supply problem. The interpretation is the user's job; the artifact provides the *measurement*.
- **Not** extrapolated. The number is computed for the window. Extrapolation to other years or to other grids is a separate step.
- **Not** a comparison across grids in v0.1.0. The cross-grid comparison is the v0.3.0 deliverable.
- **Not** a forecast. A trend over time is computable but not predicted.

## Known limitations and what v0.1.0 does *not* do

- **Single grid (CAISO).** PJM and ERCOT are not in v0.1.0.
- **Single month (June 2024).** A 7-day window is what the API returns cleanly; one month is the smallest useful unit for the capture-ratio statistic to stabilize.
- **No separation of dispatchable by fuel type.** Coal vs gas vs nuclear all enter the "dispatchable" bucket. Splitting them is v0.2.0.
- **No identification of "the" renewable price.** The CAISO "system marginal energy" component is used as a proxy for what renewables see; in practice renewables see a *net* of curtailment and congestion. The GHG component (CAISO's carbon adder) is also included.
- **No cost-of-dispatchability comparison to Lazard LCOE+.** The premium number is in $/MWh, but the substitution-decision cost is in *capital $/kW*. The link is a v0.3.0 deliverable.

## Stop-loss

**FNI-style 90-day stop-loss.** If v0.1.0 has no external references by **2026-09-14** (90 days from v0.3.0 of FNI, which is the anchor point), the project archives. The artifact is meant to be a *reference number* that other work can cite; if nothing cites it, the work is moot.

## What is *verified* as of v0.1.0

- ✅ CAISO DAM LMP CSV download via OASIS SingleZip API works.
- ✅ All 5 LMP types returned: LMP, MCC, MCE, MCL, MGHG.
- ✅ Real $/MWh values: e.g., TH_NP15_GEN-APND DAM 2024-06-01 14:00 GMT = $1.99/MWh (LMP), with $4.51 congestion, -$0.44 energy, -$0.02 loss, $0.00 GHG.
- ✅ Pandas/pyarrow environment builds and runs.

## What is *not verified* and is the next-step risk

- ⚠️ A full 30-day pull (need to confirm the 30-day cap is real vs. 7-day for some queries).
- ⚠️ The capture-ratio computation produces stable statistics from one month of data.
- ⚠️ The headline "dispatchability premium" is large enough to be interpretable.
- ⚠️ Adding PJM and ERCOT requires either API keys or browser-rendered pages; may be deferred.
