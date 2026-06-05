"""Parse GPX files into flat lists of TrackPoints.

This is the canonical parser for the entire gpx_analyst suite.
All subpackages import TrackPoint and parse_gpx from here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import gpxpy


@dataclass
class TrackPoint:
    lat: float
    lon: float
    ele: float
    time: Optional[datetime]
    power: Optional[float] = field(default=None)  # watts; from GPX extension or estimated


def parse_gpx(path: str | Path) -> List[TrackPoint]:
    """
    Parse a GPX file and return a flat list of TrackPoints.

    Supports tracks, routes, and waypoints (tried in that order).
    Reads the Garmin/Wahoo power extension (gpxtpx:PowerInWatts or
    TrackPointExtension power) when present.
    Raises ValueError if no points are found.
    """
    path = Path(path)
    with path.open("r", encoding="utf-8") as fh:
        gpx = gpxpy.parse(fh)

    points: List[TrackPoint] = []

    def _power(pt: gpxpy.gpx.GPXTrackPoint) -> Optional[float]:
        """Extract power in watts from GPX extension data if available."""
        if not pt.extensions:
            return None
        # Garmin Training Center / Wahoo extension: <power>NNN</power>
        for ext in pt.extensions:
            tag = ext.tag.lower() if hasattr(ext, "tag") else ""
            if "power" in tag:
                try:
                    return float(ext.text)
                except (TypeError, ValueError):
                    pass
        return None

    def _add(pt: gpxpy.gpx.GPXTrackPoint) -> None:
        points.append(
            TrackPoint(
                lat=pt.latitude,
                lon=pt.longitude,
                ele=pt.elevation or 0.0,
                time=pt.time,
                power=_power(pt),
            )
        )

    for track in gpx.tracks:
        for segment in track.segments:
            for pt in segment.points:
                _add(pt)

    if not points:
        for route in gpx.routes:
            for pt in route.points:
                _add(pt)

    if not points:
        for pt in gpx.waypoints:
            _add(pt)

    if not points:
        raise ValueError(f"No track points found in '{path}'")

    return points
