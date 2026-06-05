"""Visualizations for mutant-performance analysis."""

from __future__ import annotations

from pathlib import Path
from typing import Tuple

from .analyzer import MutantPerformanceResult


def visualize(
    result: MutantPerformanceResult,
    output_dir: Path,
) -> Tuple[Path, Path]:
    """Render both outputs; return (timeseries_path, scatter_path)."""
    ts_path = visualize_timeseries(result, output_dir / "mutant_perf_timeseries.png")
    sc_path = visualize_scatter(result, output_dir / "mutant_perf_scatter.png")
    return ts_path, sc_path


def visualize_timeseries(
    result: MutantPerformanceResult,
    output_path: Path,
) -> Path:
    """
    Dual-axis matplotlib plot:
      Left axis  (blue):  30-min normalised power (W) over race time
      Right axis (orange): accumulated sleep debt (hours) over race time

    Sleep periods are shaded grey.
    Performance phases (fresh / fatigued / depleted / zombie) are shown
    as coloured bands in the background.
    Correlation r and p-value are annotated in the corner.

    Returns path to saved PNG.
    """
    raise NotImplementedError(
        "mutant_performance.visualizer.visualize_timeseries is not yet implemented."
    )


def visualize_scatter(
    result: MutantPerformanceResult,
    output_path: Path,
) -> Path:
    """
    Scatter plot: X = sleep debt (h), Y = normalised power (W).

    Points are coloured by performance phase.
    A linear regression line with 95 % confidence interval is overlaid.
    The detected breakpoint (if any) is marked with a vertical dashed line.
    Pearson r and Spearman ρ are annotated.

    Returns path to saved PNG.
    """
    raise NotImplementedError(
        "mutant_performance.visualizer.visualize_scatter is not yet implemented."
    )
