"""
compute_capture_ratios.py — Compute the dispatchability premium from raw LMPs.

Reads data/raw/caiso_lmp_YYYY_MM.csv.gz, computes capture ratios per node,
and writes results/caiso_dispatchability_premium_YYYY_MM.csv with the
headline numbers.

Methodology (see docs/methodology.md):
  capture_ratio(n) = mean_t [ LMP(n, t) / LMP_grid_average(t) ]
  capture_ratio_renewable = mean over renewable nodes
  capture_ratio_dispatchable = mean over dispatchable nodes
  dispatchability_premium = capture_ratio_dispatchable - capture_ratio_renewable

For CAISO DAM, the trading-hub "GEN-APND" nodes are pricing nodes that
represent the *aggregate* of generation dispatch at that hub. We treat:
  - TH_NP15_GEN-APND, TH_SP15_GEN-APND, TH_ZP26_GEN-APND as proxies for
    "dispatchable hub price" (since the hub is net of all generation,
    including solar, the LMP here is NOT a clean "dispatchable" signal,
    but in the absence of node-level fuel-type tagging in v0.1.0 it is
    the best we have).
  - For v0.1.0, we compute the *capture ratio spread* as the simple
    spread of capture ratios across the three hubs. This is an *upper
    bound* on the true dispatchability premium because each hub's
    LMP is a mix of solar, gas, and imports.
  - A cleaner v0.2.0 will use EIA-930 to split LMP by fuel type.
"""

import argparse
import sys
from pathlib import Path

import pandas as pd

GRID_HOUR_COLS = ["OPR_DT", "OPR_HR"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", required=True, help="Path to raw LMP CSV.gz")
    parser.add_argument("--out-csv", required=True, help="Output CSV path for capture-ratio summary")
    parser.add_argument("--out-md", required=True, help="Output Markdown path for the human-readable summary")
    args = parser.parse_args()

    print(f"Reading {args.raw}")
    df = pd.read_csv(args.raw, compression="gzip")
    print(f"Rows: {len(df)}")
    print(f"LMP types: {df['LMP_TYPE'].value_counts().to_dict()}")
    nodes = sorted(df["NODE_ID"].unique().tolist())
    print(f"Nodes: {nodes}")

    # Pivot: rows are (date, hour), columns are (node, LMP type)
    pivot = df.pivot_table(
        index=GRID_HOUR_COLS,
        columns=["NODE_ID", "LMP_TYPE"],
        values="MW",
        aggfunc="first",
    )
    pivot = pivot.sort_index()
    print(f"\nPivoted shape: {pivot.shape}")

    # Extract just the LMP (total) for the three nodes
    lmp_per_node = pivot.xs("LMP", level="LMP_TYPE", axis=1)
    print(f"\nLMP per node: {lmp_per_node.shape}")

    # Grid-average proxy: simple mean across nodes (any consistent per-hour
    # normalization cancels out in the ratio)
    grid_avg = lmp_per_node.mean(axis=1)

    # Capture ratio per node per hour = node LMP / grid average
    capture_ratios = lmp_per_node.div(grid_avg, axis=0)
    capture_ratios = capture_ratios.dropna()

    print(f"\nCapture ratios computed: {len(capture_ratios)} hours")
    print(capture_ratios.describe())

    # Summary per node
    summary = capture_ratios.describe().T[["mean", "std", "min", "max", "50%"]].rename(columns={"50%": "median"})
    summary = summary.rename_axis("node").reset_index()
    summary.to_csv(args.out_csv, index=False)
    print(f"\nSaved summary to {args.out_csv}")

    # Headline numbers — idxmax/idxmin on a Series with the node as index label
    mean_cr = summary.set_index("node")["mean"]
    premium_proxy = mean_cr.max() - mean_cr.min()
    highest_cr_node = mean_cr.idxmax()
    lowest_cr_node = mean_cr.idxmin()
    highest_cr_value = mean_cr.max()
    lowest_cr_value = mean_cr.min()

    # Markdown write-up
    md_lines = [
        "# CAISO Dispatchability Premium — Summary",
        "",
        f"**Window:** {df['OPR_DT'].min()} to {df['OPR_DT'].max()}",
        f"**Market:** CAISO Day-Ahead Market (DAM)",
        f"**Hours in window:** {len(capture_ratios)}",
        f"**Nodes:** {list(capture_ratios.columns)}",
        "",
        "## Headline",
        "",
        f"- **Capture-ratio spread:** {premium_proxy:.4f} (max − min across nodes)",
        f"- **Highest capture ratio:** `{highest_cr_node}` = {highest_cr_value:.4f}",
        f"- **Lowest capture ratio:** `{lowest_cr_node}` = {lowest_cr_value:.4f}",
        "",
        "## Per-node statistics (capture ratio = node LMP / grid-average LMP)",
        "",
        "| Node | mean | std | min | max | median |",
        "|-----|------|-----|-----|-----|--------|",
    ]
    for _, row in summary.iterrows():
        md_lines.append(
            f"| `{row['node']}` | {row['mean']:.4f} | {row['std']:.4f} | {row['min']:.4f} | {row['max']:.4f} | {row['median']:.4f} |"
        )
    md_lines.extend([
        "",
        "## What this means (and doesn't)",
        "",
        "A capture ratio of 1.0 means the node captures exactly the grid-average price.",
        "A capture ratio > 1.0 means the node tends to be dispatched in higher-price hours",
        "(because the marginal unit in those hours is more expensive).",
        "A capture ratio < 1.0 means the node tends to be dispatched in lower-price hours",
        "(e.g., when solar is abundant).",
        "",
        "**Caveat (v0.1.0):** the three CAISO trading-hub nodes are *aggregates* of",
        "many generators (solar + gas + nuclear + imports). We have *not* yet split",
        "by fuel type. The capture-ratio spread is therefore an *upper bound* on",
        "the true dispatchability premium (between fuel types). v0.2.0 will use",
        "EIA-930 hourly generation-by-fuel-type to disambiguate.",
        "",
        "## Reproducibility",
        "",
        "- **Data source:** CAISO OASIS PRC_LMP (DAM, version 12, CSV format 6)",
        "- **Pipeline:** `scripts/fetch_caiso_dam_lmp.py` → `scripts/compute_capture_ratios.py`",
        "- **Methodology:** `docs/methodology.md`",
        "- **Reproducibility:** all data is public, all code is in this repository",
        "",
    ])
    Path(args.out_md).write_text("\n".join(md_lines))
    print(f"Saved write-up to {args.out_md}")


if __name__ == "__main__":
    main()
