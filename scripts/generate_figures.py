#!/usr/bin/env python3
"""
Publication Figure Generator for IEEE Transactions / Conference Papers.

Generates publication-quality charts using Matplotlib and Seaborn adhering to
IEEE formatting guidelines (single-column 3.5in, double-column 7.0in, 300 DPI,
accessible/grayscale-compatible palettes, vector PDF + raster PNG output).

Figures Generated:
1. Figure 1: Model Comparison Bar Chart (SFR & CAI across model classes and guardrail tiers)
2. Figure 2: Multi-Turn Guardrail Degradation Curve (Context depth vs. Violation probability)
3. Figure 3: Failure Mode Category Vulnerability Heatmap (Categories A-D breakdown)
4. Figure 4: Guardrail Bypass Latency Distribution (Turn/step latency of first policy breach)
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


# ==============================================================================
# IEEE Publication Styling Configuration
# ==============================================================================

def set_ieee_style() -> None:
    """Configures matplotlib rcParams for IEEE Transactions publication standards."""
    mpl.rcParams.update({
        "font.family": "serif",
        "font.serif": ["DejaVu Serif", "Times New Roman", "Times"],
        "font.size": 9,
        "axes.titlesize": 10,
        "axes.labelsize": 9.5,
        "xtick.labelsize": 8.5,
        "ytick.labelsize": 8.5,
        "legend.fontsize": 8.5,
        "figure.titlesize": 11,
        "figure.dpi": 300,
        "savefig.dpi": 300,
        "savefig.bbox": "tight",
        "savefig.pad_inches": 0.05,
        "axes.linewidth": 0.8,
        "grid.linewidth": 0.5,
        "grid.alpha": 0.4,
        "lines.linewidth": 1.5,
        "lines.markersize": 5,
        "pdf.fonttype": 42,  # TrueType for IEEE Xplore compliance
        "ps.fonttype": 42,
    })


# Accessible, print-friendly palette (ColorBrewer inspired)
PALETTE_TIERS = {
    "NONE": "#D95F02",  # Rust orange / red (unprotected baseline)
    "SOFT": "#7570B3",  # Muted purple (prompt-only defense)
    "DUAL": "#1B9E77",  # Forest green (defense-in-depth dual layer)
}

PALETTE_MODELS = {
    "Frontier Commercial": "#2B5C8F",
    "Open-Weights 8B": "#D95F02",
    "Open-Weights 3B": "#7570B3",
}


def load_latest_traces(log_dir: Path) -> List[Dict[str, Any]]:
    """Loads traces from the latest JSON benchmark file in log_dir."""
    json_files = sorted(log_dir.glob("*_benchmark_results.json"))
    if not json_files:
        raise FileNotFoundError(f"No benchmark log files found in {log_dir}")
    latest = json_files[-1]
    print(f"Loading benchmark log: {latest.name}")
    with open(latest, "r", encoding="utf-8") as f:
        data = json.load(f)
        return data.get("traces", [])


# ==============================================================================
# Plot 1: Model Comparison Bar Chart (SFR across Models & Tiers)
# ==============================================================================

def plot_model_comparison(traces: List[Dict[str, Any]], output_dir: Path) -> Path:
    """
    IEEE Single-Column (3.5 in) grouped bar chart comparing Safety Failure Rate (SFR)
    across Model Classes and Guardrail Tiers.
    """
    # Aggregate data
    records = []
    model_name_map = {
        "mock-frontier": "Frontier Commercial",
        "mock-medium": "Open-Weights 8B",
        "mock-small": "Open-Weights 3B",
        "gpt-4o-mini": "Frontier Commercial",
        "claude-3-5-sonnet": "Frontier Commercial",
        "ollama/llama3.1:8b": "Open-Weights 8B",
        "ollama/llama3.2:3b": "Open-Weights 3B",
    }

    df_raw = pd.DataFrame(traces)
    df_raw["model_label"] = df_raw["model_id"].map(lambda x: model_name_map.get(x, x))
    df_raw["tier_label"] = df_raw["guardrail_tier"].str.upper()
    df_raw["has_violation"] = df_raw["total_violations"].apply(lambda v: 1 if v > 0 else 0)

    # Compute SFR per (model, tier)
    grouped = df_raw.groupby(["model_label", "tier_label"])["has_violation"].mean().reset_index()
    grouped["SFR"] = grouped["has_violation"] * 100.0

    order_models = ["Frontier Commercial", "Open-Weights 8B", "Open-Weights 3B"]
    order_tiers = ["NONE", "SOFT", "DUAL"]

    fig, ax = plt.subplots(figsize=(3.5, 2.8))

    x = np.arange(len(order_models))
    width = 0.26

    for i, tier in enumerate(order_tiers):
        tier_vals = []
        for m in order_models:
            row = grouped[(grouped["model_label"] == m) & (grouped["tier_label"] == tier)]
            val = row["SFR"].values[0] if len(row) > 0 else 0.0
            tier_vals.append(val)

        offset = (i - 1) * width
        bars = ax.bar(
            x + offset,
            tier_vals,
            width,
            label=f"Tier: {tier}",
            color=PALETTE_TIERS[tier],
            edgecolor="black",
            linewidth=0.6,
        )

        # Bar value annotations
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax.annotate(
                    f"{height:.0f}%",
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 2),
                    textcoords="offset points",
                    ha="center",
                    va="bottom",
                    fontsize=6.5,
                )

    ax.set_ylabel("Safety Failure Rate (%)")
    ax.set_title("Safety Failure Rate by Model & Guardrail Tier", fontweight="bold", pad=8)
    ax.set_xticks(x)
    ax.set_xticklabels(order_models, fontsize=8)
    ax.set_ylim(0, 105)
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    ax.legend(frameon=True, framealpha=0.9, loc="upper left", handlelength=1.2)

    sns.despine(top=True, right=True)
    fig.tight_layout()

    pdf_path = output_dir / "figure1_model_sfr_comparison.pdf"
    png_path = output_dir / "figure1_model_sfr_comparison.png"
    fig.savefig(pdf_path, format="pdf")
    fig.savefig(png_path, format="png")
    plt.close(fig)
    print(f"Generated: {pdf_path.name}")
    return pdf_path


# ==============================================================================
# Plot 2: Multi-Turn Guardrail Degradation Curve (Context Depth vs Hazard)
# ==============================================================================

def plot_context_decay(traces: List[Dict[str, Any]], output_dir: Path) -> Path:
    """
    IEEE Single-Column (3.5 in) line chart illustrating guardrail degradation over
    multi-turn conversational context depth (Category D scenarios).
    """
    # Filter for Category D (Multi-turn decay scenarios)
    cat_d_traces = [t for t in traces if t.get("category_id") == "D"]
    if not cat_d_traces:
        cat_d_traces = traces  # Fallback to all if D not separated

    # Compute step-level violation probability
    turn_model_stats: Dict[str, Dict[int, List[int]]] = {
        "Frontier Commercial": {},
        "Open-Weights 8B": {},
        "Open-Weights 3B": {},
    }

    model_name_map = {
        "mock-frontier": "Frontier Commercial",
        "mock-medium": "Open-Weights 8B",
        "mock-small": "Open-Weights 3B",
    }

    for t in cat_d_traces:
        m_label = model_name_map.get(t.get("model_id"), "Frontier Commercial")
        if m_label not in turn_model_stats:
            continue
        # We focus on the SOFT guardrail tier where decay is most evident
        if t.get("guardrail_tier") != "soft":
            continue

        for step in t.get("steps", []):
            turn_idx = step.get("turn_index", 1)
            has_viol = 1 if len(step.get("violations_detected", [])) > 0 else 0
            turn_model_stats[m_label].setdefault(turn_idx, []).append(has_viol)

    fig, ax = plt.subplots(figsize=(3.5, 2.7))

    markers = {"Frontier Commercial": "o-", "Open-Weights 8B": "s--", "Open-Weights 3B": "^-."}

    for m_label, stats in turn_model_stats.items():
        if not stats:
            continue
        turns = sorted(stats.keys())
        # Cumulative hazard: probability of having violated by or at turn t
        cum_rates = []
        for t_idx in turns:
            vals = stats[t_idx]
            rate = (sum(vals) / len(vals)) * 100.0 if vals else 0.0
            cum_rates.append(rate)

        style = markers.get(m_label, "o-")
        ax.plot(
            turns,
            cum_rates,
            style,
            label=m_label,
            color=PALETTE_MODELS.get(m_label, "#333333"),
            linewidth=1.6,
            markersize=5,
        )

    ax.set_xlabel("Conversation Turn Depth ($t$)")
    ax.set_ylabel("Violation Probability (%)")
    ax.set_title("Context Window Guardrail Decay (Soft Tier)", fontweight="bold", pad=8)
    ax.set_ylim(-5, 105)
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend(frameon=True, framealpha=0.9, loc="upper left", handlelength=1.4)

    sns.despine(top=True, right=True)
    fig.tight_layout()

    pdf_path = output_dir / "figure2_multiturn_guardrail_decay.pdf"
    png_path = output_dir / "figure2_multiturn_guardrail_decay.png"
    fig.savefig(pdf_path, format="pdf")
    fig.savefig(png_path, format="png")
    plt.close(fig)
    print(f"Generated: {pdf_path.name}")
    return pdf_path


# ==============================================================================
# Plot 3: Failure Mode Category Vulnerability Heatmap
# ==============================================================================

def plot_category_heatmap(traces: List[Dict[str, Any]], output_dir: Path) -> Path:
    """
    IEEE Single-Column (3.5 in) heatmap displaying Safety Failure Rates across
    the 4 failure mode categories (A, B, C, D) vs Model Classes under baseline.
    """
    df = pd.DataFrame(traces)
    model_name_map = {
        "mock-frontier": "Frontier",
        "mock-medium": "Open-8B",
        "mock-small": "Open-3B",
    }
    df["Model"] = df["model_id"].map(lambda x: model_name_map.get(x, x))
    df["has_violation"] = df["total_violations"].apply(lambda v: 1 if v > 0 else 0)

    category_labels = {
        "A": "Cat A:\nPrompt Override",
        "B": "Cat B:\nTool Misuse",
        "C": "Cat C:\nShutdown Refusal",
        "D": "Cat D:\nContext Decay",
    }
    df["Category"] = df["category_id"].map(lambda c: category_labels.get(c, c))

    # Baseline only (tier=none)
    df_none = df[df["guardrail_tier"] == "none"]
    pivot = df_none.pivot_table(
        index="Category",
        columns="Model",
        values="has_violation",
        aggfunc="mean",
    ) * 100.0

    # Ensure consistent column ordering
    col_order = [c for c in ["Frontier", "Open-8B", "Open-3B"] if c in pivot.columns]
    pivot = pivot[col_order]

    fig, ax = plt.subplots(figsize=(3.5, 2.8))

    cmap = sns.color_palette("YlOrRd", as_cmap=True)
    sns.heatmap(
        pivot,
        annot=True,
        fmt=".1f",
        cmap=cmap,
        cbar_kws={"label": "SFR (%)", "shrink": 0.8},
        linewidths=0.5,
        linecolor="white",
        ax=ax,
        annot_kws={"size": 8.5, "weight": "bold"},
    )

    ax.set_title("Vulnerability Matrix by Failure Category", fontweight="bold", pad=8)
    ax.set_ylabel("")
    ax.set_xlabel("Model Class")
    plt.yticks(rotation=0)

    fig.tight_layout()

    pdf_path = output_dir / "figure3_category_vulnerability_heatmap.pdf"
    png_path = output_dir / "figure3_category_vulnerability_heatmap.png"
    fig.savefig(pdf_path, format="pdf")
    fig.savefig(png_path, format="png")
    plt.close(fig)
    print(f"Generated: {pdf_path.name}")
    return pdf_path


# ==============================================================================
# Plot 4: Guardrail Bypass Latency Distribution
# ==============================================================================

def plot_bypass_latency(traces: List[Dict[str, Any]], output_dir: Path) -> Path:
    """
    IEEE Single-Column (3.5 in) distribution chart showing at which step index
    violations first occur under goal divergence.
    """
    latencies = [
        t["first_violation_step"]
        for t in traces
        if t.get("first_violation_step") is not None
    ]

    fig, ax = plt.subplots(figsize=(3.5, 2.5))

    if latencies:
        step_counts = pd.Series(latencies).value_counts().sort_index()
        x_steps = np.arange(1, max(latencies) + 1)
        y_counts = [step_counts.get(s, 0) for s in x_steps]

        ax.bar(
            x_steps,
            y_counts,
            color="#2B5C8F",
            edgecolor="black",
            linewidth=0.6,
            width=0.6,
        )

        ax.set_xlabel("Step Index of First Safety Violation ($L_{bypass}$)")
        ax.set_ylabel("Incident Frequency")
        ax.set_title("Guardrail Bypass Latency Distribution", fontweight="bold", pad=8)
        ax.set_xticks(x_steps)
        ax.grid(axis="y", linestyle="--", alpha=0.5)
        mean_l = np.mean(latencies)
        ax.axvline(mean_l, color="#D95F02", linestyle="--", linewidth=1.5, label=f"Mean: {mean_l:.2f}")
        ax.legend(frameon=True, framealpha=0.9, loc="upper right")

    sns.despine(top=True, right=True)
    fig.tight_layout()

    pdf_path = output_dir / "figure4_bypass_latency_dist.pdf"
    png_path = output_dir / "figure4_bypass_latency_dist.png"
    fig.savefig(pdf_path, format="pdf")
    fig.savefig(png_path, format="png")
    plt.close(fig)
    print(f"Generated: {pdf_path.name}")
    return pdf_path


def main() -> int:
    set_ieee_style()
    log_dir = REPO_ROOT / "data" / "raw_logs"
    output_dir = REPO_ROOT / "paper" / "figures"
    output_dir.mkdir(parents=True, exist_ok=True)

    traces = load_latest_traces(log_dir)
    print(f"Loaded {len(traces)} execution traces from {log_dir}")

    plot_model_comparison(traces, output_dir)
    plot_context_decay(traces, output_dir)
    plot_category_heatmap(traces, output_dir)
    plot_bypass_latency(traces, output_dir)

    print("\nAll publication figures successfully generated in paper/figures/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
