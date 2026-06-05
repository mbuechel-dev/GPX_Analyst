"""Suspicious-stops analyzer — score stationary periods for resupply likelihood."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from gpx_analyst.core.geo import StopEpoch
from gpx_analyst.core.parser import TrackPoint


@dataclass
class ScoredStop:
    """A detected stop with its suspicion score and contributing signals."""
    epoch: StopEpoch
    score: float                            # 0.0 – 1.0
    poi_match: bool                         # within poi_radius_m of a vehicle POI
    poi_tags: List[str]                     # matched OSM tags, e.g. ["amenity=parking"]
    duration_signal: float                  # 0.0 – 1.0 component
    departure_jerk_signal: float            # 0.0 – 1.0 component
    racing_hours_signal: float              # 0.0 – 1.0 component
    coincident_riders: List[str]            # other rider labels stopped nearby
    classification: str                     # "normal" | "noteworthy" | "suspicious" | "highly_suspicious"


@dataclass
class SuspiciousStopsResult:
    """Full analysis result for one or more riders."""
    rider_labels: List[str]
    stops_by_rider: dict[str, List[ScoredStop]]


def analyze(
    tracks: List[List[TrackPoint]],
    labels: List[str],
    min_stop_duration_s: float = 600.0,
    poi_radius_m: float = 50.0,
    coincidence_radius_m: float = 200.0,
    coincidence_window_min: float = 15.0,
    osm_cache_dir: Optional[Path] = None,
    excluded_checkpoints: Optional[List[dict]] = None,
) -> SuspiciousStopsResult:
    """
    Score each stationary period in *tracks* for suspicious-stop likelihood.

    Parameters
    ----------
    tracks                : list of parsed tracks (one per rider)
    labels                : display labels matching *tracks*
    min_stop_duration_s   : minimum stop length to analyse (seconds)
    poi_radius_m          : radius for OSM POI match (metres)
    coincidence_radius_m  : radius for multi-rider coincidence check
    coincidence_window_min: time window for multi-rider coincidence
    osm_cache_dir         : directory for cached Overpass API responses
    excluded_checkpoints  : list of dicts with keys: lat, lon, radius_m,
                            window_start, window_end (known service checkpoints)

    Returns
    -------
    SuspiciousStopsResult

    See README.md for the full algorithm and scoring design.
    """
    raise NotImplementedError(
        "suspicious_stops.analyzer.analyze is not yet implemented. "
        "See gpx_analyst/suspicious_stops/README.md for the algorithm design."
    )
