"""Geospatial helpers shared across all gpx_analyst subpackages.

Provides:
- Coordinate projection utilities (equirectangular, Haversine)
- Polyline distance queries
- Stop / stationary-period detection
- Multi-track time-alignment and interpolation
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional, Sequence, Tuple

import numpy as np

from .parser import TrackPoint


# ---------------------------------------------------------------------------
# Coordinate projection
# ---------------------------------------------------------------------------

def to_meters(
    lats: np.ndarray,
    lons: np.ndarray,
    lat0: float,
    lon0: float,
) -> np.ndarray:
    """
    Equirectangular projection to approximate (x, y) offsets in metres.

    Accurate to < 0.5 % for extents up to ~200 km.  Suitable for all
    distance calculations within a single race/event bounding box.

    Parameters
    ----------
    lats, lons : (N,) arrays of latitude / longitude in decimal degrees
    lat0, lon0 : origin of projection (typically the centroid of all points)

    Returns
    -------
    (N, 2) array of [x_east, y_north] in metres
    """
    R = 6_371_000.0
    x = R * np.radians(lons - lon0) * np.cos(np.radians(lat0))
    y = R * np.radians(lats - lat0)
    return np.column_stack([x, y])


def haversine_distance(
    lat1: float, lon1: float,
    lat2: float, lon2: float,
) -> float:
    """
    Great-circle distance between two points in metres (Haversine formula).

    Use this when you need accurate distances independent of a local projection
    origin — e.g. comparing distant segments or computing total track length.
    """
    R = 6_371_000.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ---------------------------------------------------------------------------
# Polyline distance query (used by compare_gpx.comparator)
# ---------------------------------------------------------------------------

def min_dist_to_polyline(
    pts: np.ndarray,
    seg_starts: np.ndarray,
    seg_ends: np.ndarray,
    batch: int,
) -> np.ndarray:
    """
    Minimum distance from each point in *pts* to the polyline defined by
    consecutive segments (seg_starts[i] -> seg_ends[i]).

    Parameters
    ----------
    pts        : (N, 2)
    seg_starts : (M, 2)
    seg_ends   : (M, 2)
    batch      : number of comparison points processed per iteration

    Returns
    -------
    (N,) array of minimum distances in the same units as the inputs.
    """
    ab = seg_ends - seg_starts                                    # (M, 2)
    ab_sq = np.einsum("mi,mi->m", ab, ab) + 1e-12                # (M,)

    deviations: list[float] = []

    for start in range(0, len(pts), batch):
        chunk = pts[start : start + batch]                        # (B, 2)
        ap = chunk[:, None, :] - seg_starts[None, :, :]          # (B, M, 2)
        t = np.einsum("nmi,mi->nm", ap, ab) / ab_sq              # (B, M)
        t = np.clip(t, 0.0, 1.0)
        closest = seg_starts[None, :, :] + t[:, :, None] * ab[None, :, :]  # (B, M, 2)
        diff = chunk[:, None, :] - closest                        # (B, M, 2)
        dists = np.sqrt(np.einsum("nmi,nmi->nm", diff, diff))     # (B, M)
        deviations.extend(dists.min(axis=1).tolist())

    return np.array(deviations)


# ---------------------------------------------------------------------------
# Stop detection
# ---------------------------------------------------------------------------

@dataclass
class StopEpoch:
    """A contiguous period where a rider was stationary or near-stationary."""
    start_time: datetime
    end_time: datetime
    lat: float          # centroid of GPS positions during the stop
    lon: float
    duration_s: float   # seconds

    @property
    def duration_min(self) -> float:
        return self.duration_s / 60.0


def detect_stops(
    track: List[TrackPoint],
    speed_threshold_ms: float = 1.0,
    min_duration_s: float = 600.0,
    min_points: int = 5,
) -> List[StopEpoch]:
    """
    Identify stationary epochs in *track*.

    A stop is a contiguous run of points where the instantaneous speed
    (derived from consecutive GPS positions and timestamps) is below
    *speed_threshold_ms* (default 1 m/s ≈ 3.6 km/h) for at least
    *min_duration_s* seconds (default 10 min).

    Points without timestamps are silently ignored; if fewer than two
    timestamped points remain the function returns an empty list.

    Parameters
    ----------
    track              : list of TrackPoint
    speed_threshold_ms : speed below which a point is considered stationary (m/s)
    min_duration_s     : minimum continuous stationary duration to report (s)
    min_points         : minimum number of points in a stop epoch

    Returns
    -------
    List of StopEpoch, ordered chronologically.

    Algorithm
    ---------
    1. Filter to timestamped points and compute per-segment speeds.
    2. Label each point as stationary (True) or moving (False).
    3. Group consecutive stationary points into candidate epochs.
    4. Discard epochs shorter than *min_duration_s* or with fewer than
       *min_points* points.
    5. Compute centroid (mean lat/lon) for each surviving epoch.
    """
    raise NotImplementedError(
        "detect_stops is not yet implemented. "
        "See gpx_analyst/core/README.md for the algorithm design."
    )


# ---------------------------------------------------------------------------
# Track interpolation
# ---------------------------------------------------------------------------

def interpolate_track(
    track: List[TrackPoint],
    target_times: Sequence[datetime],
    method: str = "linear",
) -> List[TrackPoint]:
    """
    Resample *track* to an arbitrary sequence of *target_times*.

    Used by riding_together and drafting to align multiple riders to a
    common time grid before computing pairwise distances or bearings.

    Parameters
    ----------
    track        : list of TrackPoint with non-None timestamps, sorted ascending
    target_times : target timestamps to interpolate to
    method       : "linear" (default) or "cubic" (scipy CubicSpline)

    Returns
    -------
    List of TrackPoint with timestamps == target_times and interpolated
    lat, lon, ele values.  Power is linearly interpolated if present.

    Notes
    -----
    - Points outside the time range of *track* are NOT extrapolated;
      the first/last known position is clamped instead.
    - Gaps larger than 5 minutes in the source track are flagged with a
      NaN elevation so downstream code can discard unreliable epochs.
    - "cubic" uses scipy.interpolate.CubicSpline independently on lat,
      lon, and ele.  It is smoother but can oscillate across large gaps.

    Algorithm (linear)
    ------------------
    1. Convert timestamps to float seconds since epoch.
    2. Build np.interp arrays for lat, lon, ele.
    3. For each target time, interpolate all three channels.
    4. Return new TrackPoint list.
    """
    raise NotImplementedError(
        "interpolate_track is not yet implemented. "
        "See gpx_analyst/core/README.md for the algorithm design."
    )
