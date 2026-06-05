"""Batch runner — discovers GPX files and dispatches analyses in parallel."""

from __future__ import annotations

import os
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import List, Optional

try:
    from tqdm import tqdm as _tqdm
    _HAS_TQDM = True
except ImportError:  # pragma: no cover
    _HAS_TQDM = False


def _progress(iterable, **kwargs):  # type: ignore[no-untyped-def]
    """Wrap iterable with tqdm if available, otherwise pass through."""
    if _HAS_TQDM:
        return _tqdm(iterable, **kwargs)
    return iterable


class BatchRunner:
    """
    Discover GPX files, group them by analysis requirements, and dispatch
    all analyses to a process pool.

    Parameters
    ----------
    paths      : explicit list of GPX file paths to process
    output_dir : root directory for all output files
    workers    : number of worker processes (default: os.cpu_count())

    Usage
    -----
    runner = BatchRunner(paths=[...], output_dir=Path("output"))
    report_path = runner.run_all()
    """

    def __init__(
        self,
        paths: List[Path],
        output_dir: Path,
        workers: Optional[int] = None,
    ) -> None:
        self.paths = [Path(p) for p in paths]
        self.output_dir = Path(output_dir)
        self.workers = workers or os.cpu_count() or 1

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run_all(self) -> Path:
        """
        Run every applicable analysis on the configured paths.

        Analysis dispatch rules:
        - suspicious-stops and mutant-perf: run on every individual file.
        - compare: run on all pairs (round-robin) if exactly 2 files; skip
          otherwise (compare requires exactly 2 files with a defined reference).
        - riding-together and drafting: run on the full set if ≥ 2 files.

        All analyses run in parallel using ProcessPoolExecutor.  Results
        are collected and rendered into a combined HTML report via Jinja2.

        Returns
        -------
        Path to the generated combined HTML report.
        """
        self.output_dir.mkdir(parents=True, exist_ok=True)
        results: dict[str, object] = {}

        futures = {}
        with ProcessPoolExecutor(max_workers=self.workers) as pool:
            # Single-file analyses
            for path in self.paths:
                futures[pool.submit(_run_suspicious_stops_single, path, self.output_dir)] = (
                    "suspicious_stops", path.stem
                )
                futures[pool.submit(_run_mutant_perf_single, path, self.output_dir)] = (
                    "mutant_perf", path.stem
                )

            # Multi-file analyses
            if len(self.paths) >= 2:
                futures[pool.submit(_run_riding_together_all, self.paths, self.output_dir)] = (
                    "riding_together", "all"
                )
                futures[pool.submit(_run_drafting_all, self.paths, self.output_dir)] = (
                    "drafting", "all"
                )

            for future in _progress(as_completed(futures), total=len(futures),
                                     desc="Running analyses"):
                key = futures[future]
                try:
                    results[str(key)] = future.result()
                except NotImplementedError:
                    results[str(key)] = {"status": "not_implemented"}
                except Exception as exc:  # noqa: BLE001
                    results[str(key)] = {"status": "error", "message": str(exc)}

        return self._render_report(results)

    # ------------------------------------------------------------------
    # Report rendering
    # ------------------------------------------------------------------

    def _render_report(self, results: dict) -> Path:
        """Render the combined HTML report using the Jinja2 template."""
        try:
            from jinja2 import Environment, FileSystemLoader, select_autoescape
        except ImportError:  # pragma: no cover
            raise ImportError(
                "jinja2 is required for the combined report. "
                "Install it with: pip install jinja2"
            )

        template_dir = Path(__file__).parent / "templates"
        env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(["html"]),
        )
        template = env.get_template("report.html.j2")
        html = template.render(
            results=results,
            output_files=list(self.output_dir.glob("**/*.html")),
        )
        report_path = self.output_dir / "report.html"
        report_path.write_text(html, encoding="utf-8")
        return report_path


# ---------------------------------------------------------------------------
# Worker functions (must be top-level for pickling with ProcessPoolExecutor)
# ---------------------------------------------------------------------------

def _run_suspicious_stops_single(path: Path, output_dir: Path) -> dict:
    from gpx_analyst.core.parser import parse_gpx
    from gpx_analyst.suspicious_stops.analyzer import analyze
    from gpx_analyst.suspicious_stops.visualizer import visualize

    track = parse_gpx(path)
    result = analyze([track], [path.stem])
    rider_dir = output_dir / "suspicious_stops" / path.stem
    rider_dir.mkdir(parents=True, exist_ok=True)
    map_path, report_path = visualize(result, rider_dir)
    return {"map": str(map_path), "report": str(report_path)}


def _run_mutant_perf_single(path: Path, output_dir: Path) -> dict:
    from gpx_analyst.core.parser import parse_gpx
    from gpx_analyst.mutant_performance.analyzer import analyze
    from gpx_analyst.mutant_performance.visualizer import visualize

    track = parse_gpx(path)
    result = analyze(track, label=path.stem)
    rider_dir = output_dir / "mutant_performance" / path.stem
    rider_dir.mkdir(parents=True, exist_ok=True)
    ts_path, sc_path = visualize(result, rider_dir)
    return {"timeseries": str(ts_path), "scatter": str(sc_path)}


def _run_riding_together_all(paths: List[Path], output_dir: Path) -> dict:
    from gpx_analyst.core.parser import parse_gpx
    from gpx_analyst.riding_together.analyzer import analyze
    from gpx_analyst.riding_together.visualizer import visualize

    tracks = [parse_gpx(p) for p in paths]
    labels = [p.stem for p in paths]
    result = analyze(tracks, labels)
    sub_dir = output_dir / "riding_together"
    sub_dir.mkdir(parents=True, exist_ok=True)
    map_path, tl_path = visualize(result, sub_dir)
    return {"map": str(map_path), "timeline": str(tl_path)}


def _run_drafting_all(paths: List[Path], output_dir: Path) -> dict:
    from gpx_analyst.core.parser import parse_gpx
    from gpx_analyst.drafting.analyzer import analyze
    from gpx_analyst.drafting.visualizer import visualize

    tracks = [parse_gpx(p) for p in paths]
    labels = [p.stem for p in paths]
    result = analyze(tracks, labels)
    sub_dir = output_dir / "drafting"
    sub_dir.mkdir(parents=True, exist_ok=True)
    map_path, tl_path = visualize(result, sub_dir)
    return {"map": str(map_path), "timeline": str(tl_path)}
