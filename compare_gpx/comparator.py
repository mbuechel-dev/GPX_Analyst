"""Compute per-point deviations between a comparison track and a reference track."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

import numpy as np

from .parser import TrackPoint


@dataclass
class ComparisonResult:
    reference_points: List[TrackPoint]
    comparison_points: List[TrackPoint]
    deviations_m: List[float]      # one value per comparison point, in metres
    cum_distances_m: List[float]   # cumulative distance along comparison track

    @property
    def max_deviation(self) -> float:
        return float(np.max(self.deviations_m))

    @property
    def mean_deviation(self) -> float:
        return float(np.mean(self.deviations_m))

    @property
    def median_deviation(self) -> float:
        return float(np.median(self.deviations_m))

    @property
    def std_deviation(self) -> float:
        return float(np.std(self.deviations_m))

    def within_threshold(self, threshold_m: float) -> float:
        """Fraction of comparison points within *threshold_m* metres of reference."""
        return float(np.mean(np.array(self.deviations_m) <= threshold_m))


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _to_meters(
    lats: np.ndarray, lons: np.ndarray, lat0: float, lon0: float
) -> np.ndarray:
    """
    Equirectangular projection to approximate (x, y) in metres.

    Accurate to < 0.5 % for extents up to ~200 km.
    """
    R = 6_371_000.0
    x = R * np.radians(lons - lon0) * np.cos(np.radians(lat0))
    y = R * np.radians(lats - lat0)
    return np.column_stack([x, y])


def _min_dist_to_polyline(
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
# Public API
# ---------------------------------------------------------------------------

def compare_tracks(
    reference: List[TrackPoint],
    comparison: List[TrackPoint],
) -> ComparisonResult:
    """
    Compute deviation of each *comparison* point from the *reference* polyline.

    The deviation is the shortest perpendicular distance (in metres) from
    the comparison point to any segment of the reference track.
    """
    ref_lats = np.array([p.lat for p in reference])
    ref_lons = np.array([p.lon for p in reference])
    cmp_lats = np.array([p.lat for p in comparison])
    cmp_lons = np.array([p.lon for p in comparison])

    lat0 = (ref_lats.mean() + cmp_lats.mean()) / 2.0
    lon0 = (ref_lons.mean() + cmp_lons.mean()) / 2.0

    ref_xy = _to_meters(ref_lats, ref_lons, lat0, lon0)  # (Nr, 2)
    cmp_xy = _to_meters(cmp_lats, cmp_lons, lat0, lon0)  # (Nc, 2)

    seg_starts = ref_xy[:-1]
    seg_ends   = ref_xy[1:]

    # Adaptive batch size: target ~50 MB of working memory per batch
    n_segs = len(seg_starts)
    batch = max(10, min(500, int(50_000_000 / max(n_segs * 16, 1))))

    deviations = _min_dist_to_polyline(cmp_xy, seg_starts, seg_ends, batch)

    diffs = np.diff(cmp_xy, axis=0)
    cum_dist = np.concatenate([[0.0], np.cumsum(np.linalg.norm(diffs, axis=1))])

    return ComparisonResult(
        reference_points=reference,
        comparison_points=comparison,
        deviations_m=deviations.tolist(),
        cum_distances_m=cum_dist.tolist(),
    )
