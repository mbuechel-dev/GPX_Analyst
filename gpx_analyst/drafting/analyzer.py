"""Draft-zone likelihood analyzer."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Tuple

from gpx_analyst.core.parser import TrackPoint


@dataclass
class DraftEpoch:
    """A contiguous period where follower was in lead's draft zone."""
    lead_rider: str
    follower: str
    start_time: datetime
    end_time: datetime
    duration_s: float
    mean_probability: float
    mean_distance_m: float
    mean_lateral_m: float
    mean_speed_ms: float
    power_deficit_pct: Optional[float]    # None if power unavailable


@dataclass
class DraftingResult:
    """Full drafting analysis for N riders."""
    rider_labels: List[str]
    epochs: List[DraftEpoch]
    total_draft_time_s: dict[Tuple[str, str], float]   # (lead, follower) → seconds
    pct_of_race: dict[Tuple[str, str], float]          # (lead, follower) → % of overlap window


def analyze(
    tracks: List[List[TrackPoint]],
    labels: List[str],
    grid_interval_s: float = 5.0,
    d_max_m: float = 25.0,
    w_max_m: float = 1.5,
    min_speed_ms: float = 5.0,
    gps_sigma_m: float = 5.0,
    prob_threshold: float = 0.5,
    min_draft_duration_s: float = 60.0,
) -> DraftingResult:
    """
    Detect drafting epochs between all pairs of riders in *tracks*.

    Parameters
    ----------
    tracks               : list of N parsed tracks (one per rider)
    labels               : display labels matching *tracks*
    grid_interval_s      : resampling resolution (seconds)
    d_max_m              : maximum total separation for draft zone (metres)
    w_max_m              : maximum lateral offset for draft zone (metres)
    min_speed_ms         : minimum speed for drafting to be meaningful (m/s)
    gps_sigma_m          : GPS horizontal error 1σ (metres)
    prob_threshold       : minimum per-timestep probability to count as drafting
    min_draft_duration_s : minimum continuous epoch to report (seconds)

    Returns
    -------
    DraftingResult

    See README.md for the full algorithm description including the
    probabilistic lateral-offset model.
    """
    raise NotImplementedError(
        "drafting.analyzer.analyze is not yet implemented. "
        "See gpx_analyst/drafting/README.md for the algorithm design."
    )
