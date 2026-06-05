"""Top-level CLI dispatcher for the gpx_analyst suite.

Entry point: gpx-analyst
Usage:
    gpx-analyst compare        FILE FILE [-o DIR] [options]
    gpx-analyst riding-together FILE [FILE ...] [-o DIR] [options]
    gpx-analyst suspicious-stops FILE [FILE ...] [-o DIR] [options]
    gpx-analyst mutant-perf    FILE [FILE ...] [-o DIR] [options]
    gpx-analyst drafting       FILE [FILE ...] [-o DIR] [options]
    gpx-analyst run-all        (--input FILE+ | --input-dir DIR) [-o DIR] [options]
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Shared input-resolution helper
# ---------------------------------------------------------------------------

def _resolve_inputs(args: argparse.Namespace) -> list[Path]:
    """
    Collect GPX file paths from --input and/or --input-dir.
    Raises SystemExit if no files are found.
    """
    paths: list[Path] = []

    if hasattr(args, "inputs") and args.inputs:
        paths.extend(args.inputs)

    if hasattr(args, "input_dir") and args.input_dir:
        found = sorted(args.input_dir.glob("**/*.gpx"))
        if not found:
            raise SystemExit(f"No .gpx files found in {args.input_dir}")
        paths.extend(found)

    if not paths:
        raise SystemExit(
            "No input files specified.  Use positional FILE arguments "
            "or --input-dir DIR."
        )
    return paths


# ---------------------------------------------------------------------------
# run-all sub-handler
# ---------------------------------------------------------------------------

def _run_all(args: argparse.Namespace) -> None:
    """Run every applicable analysis and write a combined HTML report."""
    from gpx_analyst.batch import BatchRunner

    paths = _resolve_inputs(args)
    output_dir: Path = args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    runner = BatchRunner(
        paths=paths,
        output_dir=output_dir,
        workers=args.workers,
    )
    report_path = runner.run_all()
    print(f"Combined report: {report_path}")


# ---------------------------------------------------------------------------
# compare sub-handler
# ---------------------------------------------------------------------------

def _run_compare(args: argparse.Namespace) -> None:
    paths = _resolve_inputs(args)
    if len(paths) != 2:
        raise SystemExit(
            f"'compare' requires exactly 2 GPX files, got {len(paths)}."
        )
    from gpx_analyst.compare_gpx.cli import main as compare_main

    # Reconstruct a Namespace that compare_gpx.cli.main expects
    compare_args = argparse.Namespace(
        reference=paths[0],
        comparison=paths[1],
        output_dir=args.output_dir,
        max_scale=getattr(args, "max_scale", None),
    )
    compare_main(compare_args)


# ---------------------------------------------------------------------------
# Delegating sub-handlers
# ---------------------------------------------------------------------------

def _run_riding_together(args: argparse.Namespace) -> None:
    from gpx_analyst.riding_together.cli import main as sub_main
    args.inputs = _resolve_inputs(args)
    sub_main(args)


def _run_suspicious_stops(args: argparse.Namespace) -> None:
    from gpx_analyst.suspicious_stops.cli import main as sub_main
    args.inputs = _resolve_inputs(args)
    sub_main(args)


def _run_mutant_perf(args: argparse.Namespace) -> None:
    from gpx_analyst.mutant_performance.cli import main as sub_main
    args.inputs = _resolve_inputs(args)
    sub_main(args)


def _run_drafting(args: argparse.Namespace) -> None:
    from gpx_analyst.drafting.cli import main as sub_main
    args.inputs = _resolve_inputs(args)
    sub_main(args)


# ---------------------------------------------------------------------------
# Shared flags added to every subparser
# ---------------------------------------------------------------------------

def _add_common_flags(p: argparse.ArgumentParser) -> None:
    p.add_argument(
        "-o", "--output-dir",
        type=Path,
        default=Path("output"),
        metavar="DIR",
        help="Directory for output files (default: ./output).",
    )
    p.add_argument(
        "--input-dir",
        type=Path,
        default=None,
        metavar="DIR",
        help="Directory to scan recursively for *.gpx files.",
    )
    p.add_argument(
        "--workers",
        type=int,
        default=None,
        metavar="N",
        help="Parallel worker processes for batch runs (default: cpu_count).",
    )


# ---------------------------------------------------------------------------
# Root parser
# ---------------------------------------------------------------------------

def build_root_parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(
        prog="gpx-analyst",
        description=(
            "GPX Analyst — a suite of analysis tools for cycling events.\n\n"
            "Run a single analysis with one of the subcommands below, or use\n"
            "'run-all' to execute all applicable analyses in one shot."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    root.add_argument(
        "--version",
        action="version",
        version="%(prog)s 0.2.0",
    )

    subs = root.add_subparsers(dest="command", metavar="COMMAND")
    subs.required = True

    # ---- compare -----------------------------------------------------------
    p_compare = subs.add_parser(
        "compare",
        help="Compare two GPX tracks and visualise deviations.",
        description="Compare two GPX tracks and visualise deviations.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p_compare.add_argument("inputs", nargs=2, type=Path, metavar="FILE",
                           help="Reference and comparison GPX files.")
    p_compare.add_argument("--max-scale", type=float, default=None, metavar="METRES")
    _add_common_flags(p_compare)
    p_compare.set_defaults(func=_run_compare)

    # ---- riding-together ---------------------------------------------------
    p_rt = subs.add_parser(
        "riding-together",
        help="Detect when multiple riders were cycling together.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p_rt.add_argument("inputs", nargs="*", type=Path, metavar="FILE",
                      help="Two or more GPX files (one per rider).")
    p_rt.add_argument("--proximity", type=float, default=100.0, metavar="METRES")
    p_rt.add_argument("--min-duration", type=float, default=300.0, metavar="SECONDS")
    _add_common_flags(p_rt)
    p_rt.set_defaults(func=_run_riding_together)

    # ---- suspicious-stops --------------------------------------------------
    p_ss = subs.add_parser(
        "suspicious-stops",
        help="Detect and score stops for illegal resupply likelihood.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p_ss.add_argument("inputs", nargs="*", type=Path, metavar="FILE",
                      help="One or more GPX files to analyse.")
    p_ss.add_argument("--min-stop", type=float, default=600.0, metavar="SECONDS")
    p_ss.add_argument("--poi-radius", type=float, default=50.0, metavar="METRES")
    p_ss.add_argument("--osm-cache", type=Path, default=None, metavar="DIR")
    _add_common_flags(p_ss)
    p_ss.set_defaults(func=_run_suspicious_stops)

    # ---- mutant-perf -------------------------------------------------------
    p_mp = subs.add_parser(
        "mutant-perf",
        help="Correlate sleep deprivation with power output.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p_mp.add_argument("inputs", nargs="*", type=Path, metavar="FILE",
                      help="One or more GPX files (one per rider).")
    p_mp.add_argument("--min-sleep", type=float, default=30.0, metavar="MINUTES")
    p_mp.add_argument("--mass", type=float, default=80.0, metavar="KG")
    _add_common_flags(p_mp)
    p_mp.set_defaults(func=_run_mutant_perf)

    # ---- drafting ----------------------------------------------------------
    p_dr = subs.add_parser(
        "drafting",
        help="Compute drafting likelihood from GPS trajectory geometry.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p_dr.add_argument("inputs", nargs="*", type=Path, metavar="FILE",
                      help="Two or more GPX files (one per rider).")
    p_dr.add_argument("--d-max", type=float, default=25.0, metavar="METRES")
    p_dr.add_argument("--w-max", type=float, default=1.5, metavar="METRES")
    p_dr.add_argument("--gps-sigma", type=float, default=5.0, metavar="METRES")
    p_dr.add_argument("--min-duration", type=float, default=60.0, metavar="SECONDS")
    _add_common_flags(p_dr)
    p_dr.set_defaults(func=_run_drafting)

    # ---- run-all -----------------------------------------------------------
    p_all = subs.add_parser(
        "run-all",
        help="Run every applicable analysis and produce a combined HTML report.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    p_all.add_argument("inputs", nargs="*", type=Path, metavar="FILE",
                       help="GPX files to analyse (or use --input-dir).")
    _add_common_flags(p_all)
    p_all.set_defaults(func=_run_all)

    return root


def main() -> None:
    parser = build_root_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
