"""Visualization of GPX track deviation results."""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Tuple

import branca.colormap as branca_cmap
import folium
from folium.plugins import MiniMap
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
import numpy as np

from .comparator import ComparisonResult


# ---------------------------------------------------------------------------
# Interactive HTML map  (folium)
# ---------------------------------------------------------------------------

def visualize_map(
    result: ComparisonResult,
    output_path: str | Path = "comparison_map.html",
    max_deviation_scale: Optional[float] = None,
) -> Path:
    """
    Save an interactive Folium map to *output_path*.

    The reference track is drawn in dashed blue.
    The comparison track is colour-coded by deviation (green -> yellow -> red).
    A colour bar legend and a statistics panel are included.
    """
    output_path = Path(output_path)

    ref_pts = result.reference_points
    cmp_pts = result.comparison_points
    devs    = np.array(result.deviations_m)

    all_lats = [p.lat for p in ref_pts] + [p.lat for p in cmp_pts]
    all_lons = [p.lon for p in ref_pts] + [p.lon for p in cmp_pts]
    center   = [float(np.mean(all_lats)), float(np.mean(all_lons))]

    m = folium.Map(location=center, zoom_start=13, tiles="OpenStreetMap")
    MiniMap(toggle_display=True).add_to(m)

    # --- Reference track ---
    ref_group = folium.FeatureGroup(name="Reference track", show=True)
    folium.PolyLine(
        [[p.lat, p.lon] for p in ref_pts],
        color="#2255CC",
        weight=4,
        opacity=0.6,
        tooltip="Reference track",
        dash_array="8 4",
    ).add_to(ref_group)
    ref_group.add_to(m)

    # --- Deviation colour map ---
    vmax = max_deviation_scale or float(np.percentile(devs, 95))
    vmax = max(vmax, 1.0)

    colormap = branca_cmap.LinearColormap(
        colors=["#1a9641", "#ffffbf", "#d7191c"],
        vmin=0.0,
        vmax=vmax,
        caption="Deviation from reference track (m)",
    )
    colormap.add_to(m)

    # --- Comparison track (one PolyLine per segment, coloured by deviation) ---
    cmp_group = folium.FeatureGroup(name="Comparison track", show=True)
    for i in range(len(cmp_pts) - 1):
        seg_dev = (devs[i] + devs[i + 1]) / 2.0
        color   = colormap(min(float(seg_dev), vmax))
        folium.PolyLine(
            [[cmp_pts[i].lat, cmp_pts[i].lon],
             [cmp_pts[i + 1].lat, cmp_pts[i + 1].lon]],
            color=color,
            weight=4,
            opacity=0.9,
            tooltip=f"Deviation: {seg_dev:.1f} m",
        ).add_to(cmp_group)
    cmp_group.add_to(m)

    # Start / end markers for comparison track
    folium.CircleMarker(
        [cmp_pts[0].lat, cmp_pts[0].lon],
        radius=7, color="black", fill=True, fill_color="lime",
        tooltip="Comparison: start",
    ).add_to(m)
    folium.CircleMarker(
        [cmp_pts[-1].lat, cmp_pts[-1].lon],
        radius=7, color="black", fill=True, fill_color="red",
        tooltip="Comparison: end",
    ).add_to(m)

    # Statistics panel (top-right overlay)
    stats_html = f"""
    <div style="
        position:fixed; top:80px; right:20px; z-index:1000;
        background:white; padding:12px 16px; border-radius:8px;
        border:1px solid #ccc; font-family:Arial,sans-serif; font-size:13px;
        box-shadow:2px 2px 6px rgba(0,0,0,.3); min-width:180px;">
      <b>Comparison statistics</b>
      <table style="margin-top:6px;border-collapse:collapse;width:100%">
        <tr><td>Max&nbsp;deviation</td>
            <td style="text-align:right"><b>{result.max_deviation:.1f}&nbsp;m</b></td></tr>
        <tr><td>Mean&nbsp;deviation</td>
            <td style="text-align:right">{result.mean_deviation:.1f}&nbsp;m</td></tr>
        <tr><td>Median&nbsp;deviation</td>
            <td style="text-align:right">{result.median_deviation:.1f}&nbsp;m</td></tr>
        <tr><td>Std&nbsp;deviation</td>
            <td style="text-align:right">{result.std_deviation:.1f}&nbsp;m</td></tr>
        <tr><td>Within&nbsp;&nbsp;5&nbsp;m</td>
            <td style="text-align:right">{result.within_threshold(5)*100:.0f}&nbsp;%</td></tr>
        <tr><td>Within&nbsp;10&nbsp;m</td>
            <td style="text-align:right">{result.within_threshold(10)*100:.0f}&nbsp;%</td></tr>
        <tr><td>Within&nbsp;25&nbsp;m</td>
            <td style="text-align:right">{result.within_threshold(25)*100:.0f}&nbsp;%</td></tr>
      </table>
    </div>
    """
    m.get_root().html.add_child(folium.Element(stats_html))

    folium.LayerControl(collapsed=False).add_to(m)
    m.save(str(output_path))
    return output_path


# ---------------------------------------------------------------------------
# Static deviation plot  (matplotlib)
# ---------------------------------------------------------------------------

def visualize_plot(
    result: ComparisonResult,
    output_path: str | Path = "comparison_plot.png",
    max_deviation_scale: Optional[float] = None,
    figsize: Tuple[int, int] = (12, 5),
) -> Path:
    """
    Save a matplotlib deviation-vs-distance plot to *output_path*.

    The line is coloured continuously by deviation magnitude.
    Threshold zones and summary statistics are annotated.
    """
    output_path = Path(output_path)

    x    = np.array(result.cum_distances_m) / 1000.0   # -> km
    y    = np.array(result.deviations_m)
    vmax = max_deviation_scale or float(np.percentile(y, 95))
    vmax = max(vmax, 1.0)

    fig, ax = plt.subplots(figsize=figsize)

    # Colour-coded line
    points   = np.column_stack([x, y]).reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)
    norm     = plt.Normalize(vmin=0, vmax=vmax)
    cmap     = matplotlib.colormaps["RdYlGn_r"]
    lc       = LineCollection(segments, cmap=cmap, norm=norm, linewidth=2.5, zorder=3)
    lc.set_array((y[:-1] + y[1:]) / 2.0)
    ax.add_collection(lc)
    fig.colorbar(lc, ax=ax, pad=0.02, label="Deviation (m)")

    # Shaded threshold zones
    y_top = max(float(y.max()) * 1.15, 30.0)
    ax.axhspan(0,  5,     color="#ccf5cc", alpha=0.35, label="< 5 m")
    ax.axhspan(5,  15,    color="#ffffcc", alpha=0.35, label="5 – 15 m")
    ax.axhspan(15, y_top, color="#ffd6cc", alpha=0.35, label="> 15 m")

    ax.set_xlim(x.min(), x.max())
    ax.set_ylim(0, y_top)
    ax.set_xlabel("Distance along comparison track (km)")
    ax.set_ylabel("Deviation from reference (m)")
    ax.set_title("GPX Track Deviation Analysis")
    ax.legend(loc="upper left", fontsize=9)
    ax.grid(True, linestyle="--", alpha=0.4)

    stats_text = (
        f"Max: {result.max_deviation:.1f} m   "
        f"Mean: {result.mean_deviation:.1f} m   "
        f"Median: {result.median_deviation:.1f} m   "
        f"Within 10 m: {result.within_threshold(10)*100:.0f} %"
    )
    ax.text(
        0.5, 0.97, stats_text,
        transform=ax.transAxes, ha="center", va="top", fontsize=9,
        bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#ccc", alpha=0.85),
    )

    plt.tight_layout()
    fig.savefig(str(output_path), dpi=150, bbox_inches="tight")
    plt.close(fig)
    return output_path


# ---------------------------------------------------------------------------
# Convenience wrapper
# ---------------------------------------------------------------------------

def visualize(
    result: ComparisonResult,
    output_dir: str | Path = ".",
    max_deviation_scale: Optional[float] = None,
) -> Tuple[Path, Path]:
    """
    Generate both the interactive map and the deviation plot.

    Returns (map_path, plot_path).
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    map_path  = visualize_map(
        result, output_dir / "comparison_map.html", max_deviation_scale
    )
    plot_path = visualize_plot(
        result, output_dir / "comparison_plot.png", max_deviation_scale
    )
    return map_path, plot_path
