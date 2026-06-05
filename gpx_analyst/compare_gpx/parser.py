"""Compatibility shim — re-exports TrackPoint and parse_gpx from gpx_analyst.core.parser.

All new code should import directly from gpx_analyst.core.parser.
"""

from gpx_analyst.core.parser import TrackPoint, parse_gpx  # noqa: F401

__all__ = ["TrackPoint", "parse_gpx"]


