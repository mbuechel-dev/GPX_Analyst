"""Parse GPX files into flat lists of track points."""

from __future__ import annotations

from dataclasses import dataclass
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


def parse_gpx(path: str | Path) -> List[TrackPoint]:
    """
    Parse a GPX file and return a flat list of TrackPoints.

    Supports tracks, routes, and waypoints (tried in that order).
    Raises ValueError if no points are found.
    """
    path = Path(path)
    with path.open("r", encoding="utf-8") as fh:
        gpx = gpxpy.parse(fh)

    points: List[TrackPoint] = []

    for track in gpx.tracks:
        for segment in track.segments:
            for pt in segment.points:
                points.append(
                    TrackPoint(
                        lat=pt.latitude,
                        lon=pt.longitude,
                        ele=pt.elevation or 0.0,
                        time=pt.time,
                    )
                )

    if not points:
        for route in gpx.routes:
            for pt in route.points:
                points.append(
                    TrackPoint(
                        lat=pt.latitude,
                        lon=pt.longitude,
                        ele=pt.elevation or 0.0,
                        time=pt.time,
                    )
                )

    if not points:
        for pt in gpx.waypoints:
            points.append(
                TrackPoint(
                    lat=pt.latitude,
                    lon=pt.longitude,
                    ele=pt.elevation or 0.0,
                    time=pt.time,
                )
            )

    if not points:
        raise ValueError(f"No track points found in '{path}'")

    return points
