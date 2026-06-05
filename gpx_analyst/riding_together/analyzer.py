"""Co-riding detection analyzer."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Tuple

from gpx_analyst.core.parser import TrackPoint


@dataclass
class ProximityEpoch:
    """A contiguous period where two riders were within proximity_threshold_m."""
    rider_a: str                # filename / label
    rider_b: str
    start_time: datetime
    end_time: datetime
    duration_min: float
    mean_dist_m: float
    min_dist_m: float
    centroid_lat: float
    centroid_lon: float
    lead_rider: Optional[str]   # rider_a or rider_b label, or None if undetermined


@dataclass
class RidingTogetherResult:
    """Full analysis result for N riders."""
    rider_labels: List[str]
    epochs: List[ProximityEpoch]                           # across all pairs
    total_together_min: dict[Tuple[str, str], float]       # pair → total minutes
    pct_of_race: dict[Tuple[str, str], Tuple[float, float]]  # pair → (pct_A, pct_B)


def analyze(
    tracks: List[List[TrackPoint]],
    labels: List[str],
    proximity_threshold_m: float = 100.0,
    min_duration_s: float = 300.0,
    grid_interval_s: float = 10.0,
    corral_exclusion_min: float = 30.0,
) -> RidingTogetherResult:
    """
    Detect epochs where any pair of riders in *tracks* were riding together.

    Parameters
    ----------
    tracks                : list of N parsed tracks (each a List[TrackPoint])
    labels                : display labels matching *tracks* (e.g. filenames)
    proximity_threshold_m : max separation to count as "together" (metres)
    min_duration_s        : minimum continuous proximity to report (seconds)
    grid_interval_s       : resampling resolution (seconds)
    corral_exclusion_min  : ignore proximity within this many minutes of
                            the common start and end

    Returns
    -------
    RidingTogetherResult

    See README.md for the full algorithm description.
    """
    raise NotImplementedError(
        "riding_together.analyzer.analyze is not yet implemented. "
        "See gpx_analyst/riding_together/README.md for the algorithm design."
    )
