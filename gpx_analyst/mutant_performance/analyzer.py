"""Mutant-performance analyzer — correlate sleep debt with power output."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from gpx_analyst.core.parser import TrackPoint
from gpx_analyst.core.power import PowerParams
from .sleep import SleepSchedule


@dataclass
class PerformanceWindow:
    """Statistics for a single 30-minute analysis window."""
    window_start: datetime
    sleep_debt_h: float
    normalised_power_w: Optional[float]
    mean_speed_ms: float
    phase: str                              # fresh | fatigued | depleted | zombie | sleeping


@dataclass
class CorrelationStats:
    pearson_r: float
    pearson_p: float
    spearman_rho: float
    spearman_p: float
    n_windows: int
    breakpoint_debt_h: Optional[float]     # sleep debt at which power drops most sharply
    breakpoint_power_drop_w: Optional[float]


@dataclass
class MutantPerformanceResult:
    rider_label: str
    sleep_schedule: SleepSchedule
    windows: List[PerformanceWindow]
    correlation: CorrelationStats
    power_by_phase: Dict[str, Optional[float]]   # phase → mean NP (W)
    speed_by_phase: Dict[str, float]             # phase → mean speed (m/s)
    had_power_extension: bool


def analyze(
    track: List[TrackPoint],
    label: str,
    power_params: Optional[PowerParams] = None,
    min_sleep_min: float = 30.0,
    np_window_min: float = 30.0,
    correlation_window_h: float = 4.0,
) -> MutantPerformanceResult:
    """
    Correlate sleep debt with power output for a single rider.

    Parameters
    ----------
    track              : parsed track with timestamps; power extension optional
    label              : display label (e.g. filename stem)
    power_params       : physical parameters for power estimation (uses defaults)
    min_sleep_min      : minimum stop to classify as sleep
    np_window_min      : window width for normalised power computation
    correlation_window_h: rolling window for time-varying Pearson r

    Returns
    -------
    MutantPerformanceResult

    See README.md for the full algorithm description.
    """
    raise NotImplementedError(
        "mutant_performance.analyzer.analyze is not yet implemented. "
        "See gpx_analyst/mutant_performance/README.md for the algorithm design."
    )
