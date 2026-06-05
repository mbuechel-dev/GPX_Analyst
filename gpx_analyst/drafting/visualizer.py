"""Visualizations for drafting analysis."""

from __future__ import annotations

from pathlib import Path
from typing import Tuple

from .analyzer import DraftingResult


def visualize(
    result: DraftingResult,
    output_dir: Path,
) -> Tuple[Path, Path]:
    """Render map and probability timeline; return (map_path, timeline_path)."""
    map_path = visualize_map(result, output_dir / "drafting_map.html")
    tl_path = visualize_timeline(result, output_dir / "drafting_timeline.png")
    return map_path, tl_path


def visualize_map(
    result: DraftingResult,
    output_path: Path,
) -> Path:
    """
    Interactive Folium map.

    - All rider tracks drawn in distinct colours.
    - Draft epochs highlighted as thick coloured polylines on the follower's
      track, colour-encoded by mean_probability (yellow = 0.5, red = 1.0).
    - Clicking an epoch shows: lead/follower labels, duration, mean
      distance, mean lateral offset, and power deficit if available.

    Returns path to saved HTML file.
    """
    raise NotImplementedError(
        "drafting.visualizer.visualize_map is not yet implemented."
    )


def visualize_timeline(
    result: DraftingResult,
    output_path: Path,
) -> Path:
    """
    Matplotlib probability timeline.

    One row per ordered pair (lead, follower).
    X-axis: race time (hours since common start).
    Y-axis (within each row): per-timestep drafting probability (0–1).
    Epochs above prob_threshold filled as coloured bands.

    Returns path to saved PNG file.
    """
    raise NotImplementedError(
        "drafting.visualizer.visualize_timeline is not yet implemented."
    )
