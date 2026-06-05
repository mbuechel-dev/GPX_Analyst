"""Command-line interface."""

from __future__ import annotations

import argparse
from pathlib import Path

from .comparator import compare_tracks
from .parser import parse_gpx
from .visualizer import visualize


def main(args: argparse.Namespace | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="compare-gpx",
        description="Compare two GPX tracks and visualize deviations.",
    )
    parser.add_argument(
        "reference",
        type=Path,
        help="Reference (source of truth) GPX file",
    )
    parser.add_argument(
        "comparison",
        type=Path,
        help="Comparison GPX file",
    )
    parser.add_argument(
        "-o", "--output-dir",
        type=Path,
        default=Path("."),
        metavar="DIR",
        help="Output directory (default: current directory)",
    )
    parser.add_argument(
        "--max-scale",
        type=float,
        default=None,
        metavar="METRES",
        help="Max deviation for colour scale (default: 95th percentile of deviations)",
    )
    args = parser.parse_args() if args is None else args

    print(f"Parsing reference:  {args.reference}")
    reference = parse_gpx(args.reference)
    print(f"  -> {len(reference)} points")

    print(f"Parsing comparison: {args.comparison}")
    comparison = parse_gpx(args.comparison)
    print(f"  -> {len(comparison)} points")

    print("Computing deviations ...")
    result = compare_tracks(reference, comparison)

    print()
    print("Results")
    print(f"  Max deviation    {result.max_deviation:>8.1f} m")
    print(f"  Mean deviation   {result.mean_deviation:>8.1f} m")
    print(f"  Median deviation {result.median_deviation:>8.1f} m")
    print(f"  Std deviation    {result.std_deviation:>8.1f} m")
    print(f"  Within  5 m      {result.within_threshold(5)*100:>7.0f} %")
    print(f"  Within 10 m      {result.within_threshold(10)*100:>7.0f} %")
    print(f"  Within 25 m      {result.within_threshold(25)*100:>7.0f} %")

    print(f"\nSaving output to {args.output_dir.resolve()} ...")
    map_path, plot_path = visualize(result, args.output_dir, args.max_scale)
    print(f"  Interactive map : {map_path}")
    print(f"  Deviation plot  : {plot_path}")


if __name__ == "__main__":
    main()
