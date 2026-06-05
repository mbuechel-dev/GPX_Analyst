"""Visualizations for riding-together analysis results."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from .analyzer import RidingTogetherResult


def visualize(
    result: RidingTogetherResult,
    output_dir: Path,
) -> tuple[Path, Path]:
    """
    Render both outputs and return (map_path, timeline_path).

    Parameters
    ----------
    result     : output of riding_together.analyzer.analyze()
    output_dir : directory where output files are written

    Returns
    -------
    (map_path, timeline_path)
    """
    map_path = visualize_map(result, output_dir / "riding_together_map.html")
    timeline_path = visualize_timeline(result, output_dir / "riding_together_timeline.png")
    return map_path, timeline_path


def visualize_map(
    result: RidingTogetherResult,
    output_path: Path,
) -> Path:
    """
    Interactive Folium map.

    - Each rider's full track drawn in a distinct colour.
    - Co-riding epochs highlighted as thick coloured polylines with tooltips
      showing duration and mean separation.
    - Circle markers at the start/end of each epoch.

    Returns the path to the saved HTML file.
    """
    raise NotImplementedError(
        "riding_together.visualizer.visualize_map is not yet implemented."
    )


def visualize_timeline(
    result: RidingTogetherResult,
    output_path: Path,
) -> Path:
    """
    Matplotlib Gantt-style timeline.

    X-axis: race time (hours since common start).
    Y-axis: one row per rider pair.
    Horizontal bars show epochs where the pair was within proximity_threshold_m.
    Bar colour encodes mean separation distance (green = close, red = barely within threshold).

    Returns the path to the saved PNG file.
    """
    raise NotImplementedError(
        "riding_together.visualizer.visualize_timeline is not yet implemented."
    )
