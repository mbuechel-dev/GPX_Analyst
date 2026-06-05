"""Visualizations for suspicious-stops analysis."""

from __future__ import annotations

from pathlib import Path

from .analyzer import SuspiciousStopsResult


def visualize(
    result: SuspiciousStopsResult,
    output_dir: Path,
) -> tuple[Path, Path]:
    """Render map and table report; return (map_path, report_path)."""
    map_path = visualize_map(result, output_dir / "suspicious_stops_map.html")
    report_path = visualize_report(result, output_dir / "suspicious_stops_report.csv")
    return map_path, report_path


def visualize_map(
    result: SuspiciousStopsResult,
    output_path: Path,
) -> Path:
    """
    Interactive Folium map.

    - Full rider tracks in light grey.
    - Stop markers colour-coded by suspicion score:
        green  (score < 0.30)
        yellow (score 0.30–0.59)
        orange (score 0.60–0.79)
        red    (score ≥ 0.80)
    - Clicking a marker shows a popup with: duration, score breakdown,
      matched OSM POI tags, and any coincident riders.
    - Matched OSM POIs shown as small grey icons.

    Returns the path to the saved HTML file.
    """
    raise NotImplementedError(
        "suspicious_stops.visualizer.visualize_map is not yet implemented."
    )


def visualize_report(
    result: SuspiciousStopsResult,
    output_path: Path,
) -> Path:
    """
    Write a CSV report with one row per scored stop.

    Columns: rider, stop_start, stop_end, duration_min, lat, lon,
             score, classification, poi_match, poi_tags,
             coincident_riders, departure_jerk_signal.

    Returns the path to the saved CSV file.
    """
    raise NotImplementedError(
        "suspicious_stops.visualizer.visualize_report is not yet implemented."
    )
