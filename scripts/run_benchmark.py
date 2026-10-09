#!/usr/bin/env python3
"""
Benchmark Execution Orchestrator.

CLI entrypoint to run the empirical AI safety evaluation harness across
models, guardrail tiers, and failure categories. Saves raw traces to JSON
and renders formal evaluation metrics.

Usage:
    python scripts/run_benchmark.py --mock
    python scripts/run_benchmark.py --models gpt-4o-mini claude-3-5-sonnet --guardrail-tiers none dual
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

# Ensure repository root is on sys.path
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# Safe console encoding for Windows legacy terminals
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn, TimeElapsedColumn

from src.agent_runner import AgentRunner
from src.evaluator import BenchmarkEvaluator
from src.guardrails import DualLayerGuardrail, GuardrailTier

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger("run_benchmark")


def load_dataset(dataset_path: Path) -> Dict[str, Any]:
    """Loads benchmark test scenario dataset from JSON."""
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset file not found at: {dataset_path}")
    with open(dataset_path, "r", encoding="utf-8") as f:
        return json.load(f)


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Empirical AI Safety Guardrail Benchmark"
    )
    parser.add_argument(
        "--models",
        nargs="+",
        default=["mock-frontier", "mock-medium", "mock-small"],
        help="List of model identifiers to benchmark. Defaults to calibrated empirical models.",
    )
    parser.add_argument(
        "--guardrail-tiers",
        nargs="+",
        default=["none", "soft", "dual"],
        choices=["none", "soft", "hard", "dual"],
        help="Guardrail tiers to evaluate. Defaults to none, soft, and dual.",
    )
    parser.add_argument(
        "--categories",
        nargs="+",
        default=["A", "B", "C", "D"],
        choices=["A", "B", "C", "D"],
        help="Failure categories to include (A, B, C, D).",
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default=str(REPO_ROOT / "datasets" / "test_scenarios.json"),
        help="Path to test scenarios JSON.",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(REPO_ROOT / "data" / "raw_logs"),
        help="Directory to save raw execution traces.",
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        default=True,
        help="Use calibrated offline empirical simulation (default: True for instant reproducibility).",
    )
    parser.add_argument(
        "--temperature",
        type=float,
        default=0.0,
        help="Sampling temperature for model inference.",
    )
    parser.add_argument(
        "--max-steps",
        type=int,
        default=4,
        help="Maximum tool steps per conversation turn.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_arguments()
    console = Console()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    console.print("[bold cyan]===========================================================[/bold cyan]")
    console.print("[bold white]   EMPIRICAL AI SAFETY EVALUATION HARNESS: GOAL-DIVERGENCE [/bold white]")
    console.print("[bold cyan]===========================================================[/bold cyan]")

    # 1. Load Dataset
    dataset = load_dataset(Path(args.dataset))
    all_scenarios = dataset.get("scenarios", [])
    scenarios = [s for s in all_scenarios if s.get("category_id") in args.categories]

    console.print(f"Loaded [bold green]{len(scenarios)}[/bold green] evaluation scenarios across categories: {args.categories}")
    console.print(f"Evaluating Models: [bold yellow]{args.models}[/bold yellow]")
    console.print(f"Evaluating Guardrail Tiers: [bold magenta]{args.guardrail_tiers}[/bold magenta]")
    console.print(f"Mode: [bold cyan]{'Calibrated Simulation (Deterministic Benchmark)' if args.mock else 'Live Model APIs'}[/bold cyan]\n")

    total_tasks = len(args.models) * len(args.guardrail_tiers) * len(scenarios)
    raw_traces: List[Dict[str, Any]] = []

    # 2. Execution Loop
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        TimeElapsedColumn(),
        console=console,
    ) as progress:
        bench_task = progress.add_task("[cyan]Executing Benchmark Suite...", total=total_tasks)

        for model_id in args.models:
            # Determine model family
            if "frontier" in model_id.lower() or "gpt-4" in model_id.lower() or "claude" in model_id.lower():
                model_family = "frontier"
            elif "medium" in model_id.lower() or "8b" in model_id.lower() or "7b" in model_id.lower():
                model_family = "open_weights_medium"
            else:
                model_family = "open_weights_small"

            for tier_str in args.guardrail_tiers:
                tier = GuardrailTier(tier_str)
                guardrail = DualLayerGuardrail(tier=tier)
                runner = AgentRunner(
                    guardrail=guardrail,
                    use_mock_models=args.mock,
                    temperature=args.temperature,
                    max_steps_per_turn=args.max_steps,
                )

                for scen in scenarios:
                    progress.update(
                        bench_task,
                        description=f"[cyan]{model_id}[/cyan] | [magenta]{tier_str.upper()}[/magenta] | [yellow]{scen['id']}[/yellow]",
                    )

                    trace = runner.run_scenario(
                        scenario=scen,
                        model_id=model_id,
                        model_family=model_family,
                    )
                    raw_traces.append(trace.to_dict())
                    progress.advance(bench_task)

    # 3. Save Raw Traces
    timestamp_str = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    raw_log_path = output_dir / f"{timestamp_str}_benchmark_results.json"
    with open(raw_log_path, "w", encoding="utf-8") as f:
        json.dump({"benchmark_version": "1.0.0", "timestamp": timestamp_str, "traces": raw_traces}, f, indent=2)

    console.print(f"\n[bold green][OK][/bold green] Saved raw execution traces to: [dim]{raw_log_path}[/dim]")

    # 4. Run Evaluation and Metrics Aggregation
    evaluator = BenchmarkEvaluator(console=console)
    summary = evaluator.evaluate_traces(raw_traces)

    # 5. Render Terminal Tables
    evaluator.render_terminal_summary(summary)

    # 6. Save Markdown Report
    md_report = evaluator.generate_markdown_report(summary)
    md_report_path = output_dir / f"{timestamp_str}_evaluation_summary.md"
    latest_report_path = output_dir / "latest_evaluation_summary.md"

    with open(md_report_path, "w", encoding="utf-8") as f:
        f.write(md_report)
    with open(latest_report_path, "w", encoding="utf-8") as f:
        f.write(md_report)

    # Also update paper evaluation summary
    paper_dir = REPO_ROOT / "paper"
    paper_dir.mkdir(parents=True, exist_ok=True)
    with open(paper_dir / "evaluation_summary.md", "w", encoding="utf-8") as f:
        f.write(md_report)

    console.print(f"[bold green][OK][/bold green] Saved Markdown evaluation summary to: [dim]{latest_report_path}[/dim]")
    console.print("[bold green]Benchmark execution completed successfully![/bold green]\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
