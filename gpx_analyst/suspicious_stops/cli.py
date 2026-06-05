"""Command-line interface for suspicious-stops analysis."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional

from gpx_analyst.core.parser import parse_gpx
from .analyzer import analyze
from .visualizer import visualize


def build_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    kwargs = dict(
        description="Detect and score stops that may indicate an illegal resupply.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    if parent is not None:
        p = parent.add_parser("suspicious-stops", **kwargs)
    else:
        p = argparse.ArgumentParser(prog="suspicious-stops", **kwargs)

    p.add_argument(
        "inputs",
        nargs="+",
        type=Path,
        metavar="FILE",
        help="One or more GPX files to analyse.",
    )
    p.add_argument(
        "-o", "--output-dir",
        type=Path,
        default=Path("output"),
        metavar="DIR",
    )
    p.add_argument(
        "--min-stop",
        type=float,
        default=600.0,
        metavar="SECONDS",
        help="Minimum stop duration to analyse.",
    )
    p.add_argument(
        "--poi-radius",
        type=float,
        default=50.0,
        metavar="METRES",
        help="Radius for OSM POI cross-reference.",
    )
    p.add_argument(
        "--osm-cache",
        type=Path,
        default=None,
        metavar="DIR",
        help="Directory for cached Overpass API responses.",
    )
    return p


def main(args: argparse.Namespace | None = None) -> None:
    if args is None:
        args = build_parser().parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)

    print("Parsing GPX files ...")
    tracks, labels = [], []
    for path in args.inputs:
        track = parse_gpx(path)
        tracks.append(track)
        labels.append(path.stem)
        print(f"  {path.name}: {len(track)} points")

    print("Analysing stops ...")
    result = analyze(
        tracks,
        labels,
        min_stop_duration_s=args.min_stop,
        poi_radius_m=args.poi_radius,
        osm_cache_dir=args.osm_cache,
    )

    print(f"Saving output to {args.output_dir.resolve()} ...")
    map_path, report_path = visualize(result, args.output_dir)
    print(f"  Map    : {map_path}")
    print(f"  Report : {report_path}")


if __name__ == "__main__":
    main()
