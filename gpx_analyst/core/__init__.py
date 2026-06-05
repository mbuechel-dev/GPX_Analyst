"""Shared data models and utilities used by all gpx_analyst subpackages."""

from .parser import TrackPoint, parse_gpx
from .geo import (
    to_meters,
    haversine_distance,
    min_dist_to_polyline,
    detect_stops,
    interpolate_track,
)
from .power import estimate_power

__all__ = [
    "TrackPoint",
    "parse_gpx",
    "to_meters",
    "haversine_distance",
    "min_dist_to_polyline",
    "detect_stops",
    "interpolate_track",
    "estimate_power",
]
