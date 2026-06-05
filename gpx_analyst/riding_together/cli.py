"""Command-line interface for riding-together analysis."""

from __future__ import annotations

import argparse
from pathlib import Path

from gpx_analyst.core.parser import parse_gpx
from .analyzer import analyze
from .visualizer import visualize


def build_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    """Return the argument parser (or subparser) for this subpackage."""
    kwargs = dict(
        description="Detect epochs where multiple riders were cycling together.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    if parent is not None:
        p = parent.add_parser("riding-together", **kwargs)
    else:
        p = argparse.ArgumentParser(prog="riding-together", **kwargs)

    p.add_argument(
        "inputs",
        nargs="+",
        type=Path,
        metavar="FILE",
        help="Two or more GPX files (one per rider). All must contain timestamps.",
    )
    p.add_argument(
        "-o", "--output-dir",
        type=Path,
        default=Path("output"),
        metavar="DIR",
        help="Directory for output files.",
    )
    p.add_argument(
        "--proximity",
        type=float,
        default=100.0,
        metavar="METRES",
        help="Max separation to count as riding together.",
    )
    p.add_argument(
        "--min-duration",
        type=float,
        default=300.0,
        metavar="SECONDS",
        help="Minimum proximity duration to report.",
    )
    return p


def main(args: argparse.Namespace | None = None) -> None:
    if args is None:
        args = build_parser().parse_args()

    if len(args.inputs) < 2:
        raise SystemExit("riding-together requires at least 2 GPX files.")

    args.output_dir.mkdir(parents=True, exist_ok=True)

    print("Parsing GPX files ...")
    tracks = []
    labels = []
    for path in args.inputs:
        track = parse_gpx(path)
        tracks.append(track)
        labels.append(path.stem)
        print(f"  {path.name}: {len(track)} points")

    print("Analysing co-riding epochs ...")
    result = analyze(
        tracks,
        labels,
        proximity_threshold_m=args.proximity,
        min_duration_s=args.min_duration,
    )

    print(f"Saving output to {args.output_dir.resolve()} ...")
    map_path, timeline_path = visualize(result, args.output_dir)
    print(f"  Map      : {map_path}")
    print(f"  Timeline : {timeline_path}")


if __name__ == "__main__":
    main()
