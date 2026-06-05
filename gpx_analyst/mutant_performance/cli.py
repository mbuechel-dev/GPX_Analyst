"""Command-line interface for mutant-performance analysis."""

from __future__ import annotations

import argparse
from pathlib import Path

from gpx_analyst.core.parser import parse_gpx
from .analyzer import analyze
from .visualizer import visualize


def build_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    kwargs = dict(
        description=(
            "Correlate sleep deprivation with power output over a multi-day "
            "ultra-cycling event."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    if parent is not None:
        p = parent.add_parser("mutant-perf", **kwargs)
    else:
        p = argparse.ArgumentParser(prog="mutant-perf", **kwargs)

    p.add_argument(
        "inputs",
        nargs="+",
        type=Path,
        metavar="FILE",
        help="One or more GPX files (one per rider). Timestamps required.",
    )
    p.add_argument(
        "-o", "--output-dir",
        type=Path,
        default=Path("output"),
        metavar="DIR",
    )
    p.add_argument(
        "--min-sleep",
        type=float,
        default=30.0,
        metavar="MINUTES",
        help="Minimum stop duration to classify as sleep.",
    )
    p.add_argument(
        "--mass",
        type=float,
        default=80.0,
        metavar="KG",
        help="Rider + bike system mass for power estimation.",
    )
    return p


def main(args: argparse.Namespace | None = None) -> None:
    if args is None:
        args = build_parser().parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)

    for path in args.inputs:
        print(f"Analysing {path.name} ...")
        track = parse_gpx(path)
        print(f"  {len(track)} points")

        result = analyze(track, label=path.stem, min_sleep_min=args.min_sleep)

        rider_dir = args.output_dir / path.stem
        rider_dir.mkdir(parents=True, exist_ok=True)
        ts_path, sc_path = visualize(result, rider_dir)
        print(f"  Time-series : {ts_path}")
        print(f"  Scatter     : {sc_path}")


if __name__ == "__main__":
    main()
