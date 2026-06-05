"""Command-line interface for drafting likelihood analysis."""

from __future__ import annotations

import argparse
from pathlib import Path

from gpx_analyst.core.parser import parse_gpx
from .analyzer import analyze
from .visualizer import visualize


def build_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    kwargs = dict(
        description=(
            "Compute the likelihood that riders were drafting each other "
            "based on GPS trajectory geometry."
        ),
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    if parent is not None:
        p = parent.add_parser("drafting", **kwargs)
    else:
        p = argparse.ArgumentParser(prog="drafting", **kwargs)

    p.add_argument(
        "inputs",
        nargs="+",
        type=Path,
        metavar="FILE",
        help="Two or more GPX files (one per rider). Timestamps required.",
    )
    p.add_argument(
        "-o", "--output-dir",
        type=Path,
        default=Path("output"),
        metavar="DIR",
    )
    p.add_argument(
        "--d-max",
        type=float,
        default=25.0,
        metavar="METRES",
        help="Max total separation to consider for draft zone.",
    )
    p.add_argument(
        "--w-max",
        type=float,
        default=1.5,
        metavar="METRES",
        help="Max lateral offset for draft zone.",
    )
    p.add_argument(
        "--gps-sigma",
        type=float,
        default=5.0,
        metavar="METRES",
        help="GPS horizontal 1σ error for probability model.",
    )
    p.add_argument(
        "--min-duration",
        type=float,
        default=60.0,
        metavar="SECONDS",
        help="Minimum epoch length to report.",
    )
    return p


def main(args: argparse.Namespace | None = None) -> None:
    if args is None:
        args = build_parser().parse_args()

    if len(args.inputs) < 2:
        raise SystemExit("drafting requires at least 2 GPX files.")

    args.output_dir.mkdir(parents=True, exist_ok=True)

    print("Parsing GPX files ...")
    tracks, labels = [], []
    for path in args.inputs:
        track = parse_gpx(path)
        tracks.append(track)
        labels.append(path.stem)
        print(f"  {path.name}: {len(track)} points")

    print("Analysing draft zones ...")
    result = analyze(
        tracks,
        labels,
        d_max_m=args.d_max,
        w_max_m=args.w_max,
        gps_sigma_m=args.gps_sigma,
        min_draft_duration_s=args.min_duration,
    )

    print(f"Saving output to {args.output_dir.resolve()} ...")
    map_path, tl_path = visualize(result, args.output_dir)
    print(f"  Map      : {map_path}")
    print(f"  Timeline : {tl_path}")


if __name__ == "__main__":
    main()
