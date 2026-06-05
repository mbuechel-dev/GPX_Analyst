# Changelog

All notable changes to this project are documented here.  
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [0.2.0] — 2026-06-05

### Summary

Major milestone: the original single-tool `compare-gpx` package has been
renamed and completely refactored into **`gpx-analyst`** — a unified suite of
GPX analysis tools for ultra-cycling event compliance and performance review.

---

### Package Rename

| Before | After |
|---|---|
| Package name | `compare-gpx` → `gpx-analyst` |
| Import root | `compare_gpx` → `gpx_analyst` |
| Top-level CLI | `compare-gpx` (sole command) → `gpx-analyst` (dispatcher) + individual commands |
| Python ≥ | 3.9 (unchanged) |

The old `compare-gpx` standalone command is preserved as a registered entry
point (`gpx_analyst.compare_gpx.cli:main`) for backwards compatibility.

---

### Added

#### `gpx_analyst` — top-level package

- `gpx_analyst/__init__.py` — package with `__version__ = "0.2.0"`.
- `gpx_analyst/cli.py` — unified `gpx-analyst` CLI dispatcher supporting
  sub-commands: `compare`, `riding-together`, `suspicious-stops`,
  `mutant-perf`, `drafting`, `run-all`.  Shared `--input-dir` flag for
  directory-based file discovery.
- `gpx_analyst/batch.py` — `BatchRunner` class; runs all analyses in parallel
  via `ProcessPoolExecutor`; renders a combined HTML report with Jinja2.
- `gpx_analyst/templates/report.html.j2` — Jinja2 template for the combined
  batch report.

#### `gpx_analyst.core` — new shared-utilities subpackage

- `core/parser.py` — canonical `TrackPoint` dataclass and `parse_gpx()`
  function, replacing the standalone `compare_gpx/parser.py`.  Added:
  - `TrackPoint.power` field (`Optional[float]`, watts).
  - Garmin/Wahoo power-extension reading (`<gpxtpx:PowerInWatts>`,
    `<power>`).
  - Support for GPX routes and waypoints in addition to tracks.
- `core/geo.py` — new module consolidating geospatial helpers shared across
  all subpackages:
  - `to_meters()` — equirectangular projection.
  - `haversine_distance()` — great-circle distance.
  - `min_dist_to_polyline()` — vectorised point-to-polyline distance
    (extracted from the original `compare_gpx` comparator).
  - `detect_stops()` — stationary-period detection returning `StopEpoch`
    objects.
  - `interpolate_track()` — resample a track to arbitrary timestamps using
    linear or cubic-spline interpolation; handles data gaps > 5 min.
- `core/power.py` — new physics-based cycling power estimator:
  - `PowerParams` dataclass (mass, Cr, CdA, ρ, drivetrain efficiency).
  - `estimate_power()` — standard cycling power equation with 60 s
    rolling-mean smoothing.
- `core/README.md` — detailed technical documentation of the core module,
  including algorithm descriptions and the full power equation in LaTeX.

#### `gpx_analyst.compare_gpx` — refactored track-deviation subpackage

Converted from a standalone top-level package into a subpackage of
`gpx_analyst`.  Internal changes:

- `parser.py` now re-exports from `gpx_analyst.core.parser` (thin shim).
- `comparator.py` — `min_dist_to_polyline` delegated to `core.geo`.
  `ComparisonResult` extended with `cum_distances_m` for the deviation
  plot.
- `visualizer.py` — added deviation peak detection and map markers;
  added `MiniMap` plugin; improved colour-bar legend; added per-segment
  hover tooltips.
- `__init__.py` — re-exports `parse_gpx`, `TrackPoint`,
  `compare_tracks`, `ComparisonResult`, `visualize`, `visualize_map`,
  `visualize_plot`.

#### `gpx_analyst.riding_together` — new co-riding detection subpackage

- `analyzer.py` — `ProximityEpoch` and `RidingTogetherResult` dataclasses;
  `analyze()` function:
  - Common time-window detection.
  - Resampling to a 10 s grid via `core.geo.interpolate_track`.
  - Pairwise Haversine distance time-series.
  - Epoch detection with start/finish corral suppression.
  - Lead-rider heuristic (lower mean power, or further ahead in direction
    of travel).
- `visualizer.py` — Folium map with co-riding segments; per-pair proximity
  timeline chart.
- `cli.py` — `riding-together` entry point.
- `README.md` — full algorithm description.

#### `gpx_analyst.suspicious_stops` — new resupply-stop detection subpackage

- `analyzer.py` — `ScoredStop` and `SuspiciousStopsResult` dataclasses;
  `analyze()` function:
  - Stop detection via `core.geo.detect_stops`.
  - OSM POI queries via `osmnx` (Overpass API); results cached to JSON.
  - Five-signal scoring model (POI match, duration, departure jerk,
    racing hours, multi-rider coincidence).
  - Known-checkpoint exclusion from a supplied list.
- `visualizer.py` — interactive Folium map colour-coded by suspicion score;
  CSV/table report.
- `cli.py` — `suspicious-stops` entry point.
- `README.md` — full algorithm, scoring weights, OSM tag table.

#### `gpx_analyst.mutant_performance` — new sleep-debt vs power subpackage

- `sleep.py` — `SleepPeriod` and `SleepSchedule` dataclasses; sleep-period
  detection from stop epochs with time-of-day filtering and micro-nap
  merging; sleep-debt accumulation formula.
- `analyzer.py` — `PerformanceWindow`, `CorrelationStats`,
  `MutantPerformanceResult` dataclasses; `analyze()` function:
  - Power series from extension data or `core.power` estimation.
  - 30-min normalised power (NP) windows.
  - Pearson r, Spearman ρ, rolling 4-hour Pearson, piecewise-linear
    breakpoint detection.
  - Performance phase classification (fresh / fatigued / depleted /
    zombie / sleeping).
- `visualizer.py` — dual-axis power + sleep-debt time-series plot; power
  vs sleep-debt scatter with regression and confidence interval.
- `cli.py` — `mutant-perf` entry point.
- `README.md` — full algorithm with LaTeX formulae for sleep debt,
  normalised power, and breakpoint detection.

#### `gpx_analyst.drafting` — new draft-zone likelihood subpackage

- `analyzer.py` — `DraftEpoch` and `DraftingResult` dataclasses; `analyze()`
  function:
  - Resampling to a 5 s grid.
  - Gaussian-weighted circular-mean heading smoothing.
  - Draft-zone geometry test (parallel/perpendicular decomposition).
  - Probabilistic lateral-offset model using normal CDF with combined GPS
    error $\sigma_{\text{GPS}}\sqrt{2}$.
  - Power-deficit validation for epochs where power data is available.
- `interpolator.py` — multi-track alignment wrapper with gap detection and
  optional Kalman filter smoothing.
- `visualizer.py` — Folium draft-epoch map; per-pair probability timeline.
- `cli.py` — `drafting` entry point.
- `README.md` — full algorithm with LaTeX geometry derivation and
  probability model.

---

### Changed

- `pyproject.toml`
  - `name`: `compare-gpx` → `gpx-analyst`.
  - `version`: `0.1.0` → `0.2.0`.
  - `description` updated to reflect the full suite.
  - `dependencies` expanded: added `pandas`, `scipy`, `statsmodels`,
    `osmnx`, `jinja2`, `tqdm`.
  - `[project.optional-dependencies]` section added (`full` extra for
    `scikit-learn`).
  - `[project.scripts]` expanded with all six entry points.
  - `[tool.setuptools.packages.find]` updated to `include = ["gpx_analyst*"]`.
- `requirements.txt` — retained as a minimal convenience file (not
  authoritative; `pyproject.toml` is the source of truth for dependencies).
- `README.md` — completely rewritten to document the full suite.

---

### Removed

- Top-level `compare_gpx/` package removed; functionality moved to
  `gpx_analyst/compare_gpx/`.
- Standalone `setup.py` / `setup.cfg` (if present) replaced by
  `pyproject.toml`-only build.

---

## [0.1.0] — (initial release)

### Added

- Standalone `compare-gpx` package:
  - `parser.py` — GPX parsing with `gpxpy`.
  - `comparator.py` — point-to-polyline deviation computation.
  - `visualizer.py` — Folium deviation map and matplotlib deviation plot.
  - `cli.py` — `compare-gpx reference.gpx comparison.gpx` command.
  - `__main__.py` — `python -m compare_gpx` entry point.
- `pyproject.toml` with minimal dependencies: `gpxpy`, `numpy`,
  `matplotlib`, `folium`, `branca`.
- `README.md` for the original `compare-gpx` tool.
