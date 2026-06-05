# gpx-analyst

**gpx-analyst** is a Python suite of GPX analysis tools built for ultra-cycling event compliance and performance analysis. It provides five specialised analysis modules — all sharing a common data model and geospatial core — accessible both as a unified CLI and as importable Python packages.

> **Current version:** 0.2.0  
> **Requires:** Python 3.9+

---

## Table of Contents

- [Overview](#overview)
- [Installation](#installation)
- [Architecture](#architecture)
- [CLI Usage](#cli-usage)
  - [Unified dispatcher: `gpx-analyst`](#unified-dispatcher-gpx-analyst)
  - [Individual CLIs](#individual-clis)
- [Subpackages](#subpackages)
  - [core](#gpx_analystcore--shared-utilities)
  - [compare\_gpx](#gpx_analystcompare_gpx--track-deviation-analysis)
  - [riding\_together](#gpx_analystriding_together--co-riding-detection)
  - [suspicious\_stops](#gpx_analystsuspicious_stops--unsupported-resupply-detection)
  - [mutant\_performance](#gpx_analystmutant_performance--sleep-debt-vs-power-output)
  - [drafting](#gpx_analystdrafting--draft-zone-likelihood-detection)
- [Batch Mode](#batch-mode)
- [Dependencies](#dependencies)

---

## Overview

| Module | Purpose | Inputs | Outputs |
|---|---|---|---|
| `compare_gpx` | Measure route deviation between two tracks | 2 GPX files | Interactive map, deviation plot |
| `riding_together` | Detect when multiple riders were travelling in proximity | 2+ GPX files (timestamped) | Proximity epochs, map, timeline chart |
| `suspicious_stops` | Flag stops with characteristics of illegal vehicle resupply | 1+ GPX files (timestamped) | Scored stop report, map, CSV |
| `mutant_performance` | Correlate sleep debt with power output degradation | 1 GPX file (timestamped) | Sleep schedule, correlation stats, plots |
| `drafting` | Detect when riders were in each other's aerodynamic draft zone | 2+ GPX files (timestamped) | Draft epochs, probability map, timeline |

---

## Installation

```bash
pip install -e .
```

For the optional scikit-learn–powered features:

```bash
pip install -e ".[full]"
```

All core dependencies (`gpxpy`, `numpy`, `matplotlib`, `folium`, `branca`, `pandas`, `scipy`, `statsmodels`, `osmnx`, `jinja2`, `tqdm`) are installed automatically.

---

## Architecture

```
gpx_analyst/
├── __init__.py          # package version
├── cli.py               # unified gpx-analyst CLI dispatcher
├── batch.py             # BatchRunner — parallel execution + combined HTML report
├── templates/
│   └── report.html.j2   # Jinja2 template for combined report
├── core/                # shared data model and utilities
│   ├── parser.py        # parse_gpx() → List[TrackPoint]
│   ├── geo.py           # projections, distances, stop/interpolation helpers
│   └── power.py         # physics-based power estimator
├── compare_gpx/         # route-deviation analysis
├── riding_together/     # co-riding detection
├── suspicious_stops/    # resupply-stop detection
├── mutant_performance/  # sleep-debt vs power correlation
└── drafting/            # draft-zone likelihood
```

Every analysis subpackage follows the same internal layout:

```
<subpackage>/
├── __init__.py
├── analyzer.py    # core algorithm + result dataclasses
├── visualizer.py  # Folium maps and matplotlib charts
└── cli.py         # argparse entry point
```

`core` has no dependency on any analysis subpackage. All analysis subpackages depend only on `core`.

---

## CLI Usage

### Unified dispatcher: `gpx-analyst`

```
gpx-analyst <command> [options]
```

| Command | Description |
|---|---|
| `compare` | Compare two GPX tracks |
| `riding-together` | Detect co-riding between multiple riders |
| `suspicious-stops` | Score stops for resupply likelihood |
| `mutant-perf` | Correlate sleep debt with power |
| `drafting` | Detect draft-zone epochs |
| `run-all` | Run all applicable analyses and produce a combined HTML report |

**Shared input options** (available on all multi-file commands):

| Flag | Description |
|---|---|
| `FILE [FILE ...]` | One or more GPX files as positional arguments |
| `--input-dir DIR` | Recursively discover all `.gpx` files in a directory |
| `-o / --output-dir DIR` | Output directory (default: `.`) |

**`run-all` options:**

| Flag | Default | Description |
|---|---|---|
| `--workers N` | `os.cpu_count()` | Number of parallel worker processes |

Example — run all analyses on a directory of rider files and produce a combined report:

```bash
gpx-analyst run-all --input-dir ./riders -o ./race_report
```

---

### Individual CLIs

Each subpackage also registers its own standalone command for direct use:

| Command | Entry point |
|---|---|
| `compare-gpx` | `gpx_analyst.compare_gpx.cli:main` |
| `riding-together` | `gpx_analyst.riding_together.cli:main` |
| `suspicious-stops` | `gpx_analyst.suspicious_stops.cli:main` |
| `mutant-perf` | `gpx_analyst.mutant_performance.cli:main` |
| `drafting` | `gpx_analyst.drafting.cli:main` |

---

## Subpackages

---

### `gpx_analyst.core` — Shared Utilities

The foundation of the entire suite. No analysis logic lives here — only the data model, geospatial helpers, and the physics-based power estimator.

#### Data Model

```python
@dataclass
class TrackPoint:
    lat:   float
    lon:   float
    ele:   float
    time:  Optional[datetime]
    power: Optional[float]      # watts — from GPX extension or estimated
```

All subpackages operate on `List[TrackPoint]`.

#### `core.parser` — `parse_gpx`

```python
from gpx_analyst.core.parser import parse_gpx, TrackPoint

points: List[TrackPoint] = parse_gpx("rider.gpx")
```

- Tries tracks → routes → waypoints in order.
- Reads Garmin/Wahoo power extensions (`<gpxtpx:PowerInWatts>` or `<power>`) when present.
- Raises `ValueError` on empty files.

#### `core.geo` — Geospatial Helpers

| Function | Description |
|---|---|
| `to_meters(lats, lons, lat0, lon0)` | Equirectangular projection to (x, y) metres; accurate to < 0.5 % for extents up to ~200 km |
| `haversine_distance(lat1, lon1, lat2, lon2)` | Great-circle distance in metres |
| `min_dist_to_polyline(pts, starts, ends, batch)` | Vectorised point-to-polyline minimum distance |
| `detect_stops(track, ...)` | Identify stationary epochs → `List[StopEpoch]` |
| `interpolate_track(track, target_times, method)` | Resample a track to arbitrary timestamps (linear or cubic spline) |

#### `core.power` — Physics-Based Power Estimator

```python
from gpx_analyst.core.power import estimate_power, PowerParams

params = PowerParams(mass_kg=75.0, CdA=0.30)
power_series = estimate_power(track, params, smooth_window_s=60.0)
```

Implements the standard cycling power equation:

$$P = \frac{1}{\eta}\left[\left(m g C_r + m g \sin\theta\right)v + \frac{1}{2}\rho\, C_{dA}\, v^3\right]$$

Used automatically by `mutant_performance` and `drafting` when a GPX file contains no power extension.

---

### `gpx_analyst.compare_gpx` — Track Deviation Analysis

Compares two GPX tracks following the same route and measures how far the comparison track deviates from the reference at every point.

#### CLI

```bash
compare-gpx reference.gpx comparison.gpx -o ./output
# or via the unified dispatcher:
gpx-analyst compare reference.gpx comparison.gpx -o ./output
```

```
Parsing reference:  reference.gpx
  -> 4821 points
Parsing comparison: comparison.gpx
  -> 3104 points
Computing deviations ...

Results
  Max deviation         42.3 m
  Mean deviation         6.1 m
  Median deviation       4.8 m
  Std deviation          5.9 m
  Within  5 m              62 %
  Within 10 m              81 %
  Within 25 m              97 %
```

| Flag | Default | Description |
|---|---|---|
| `-o / --output-dir DIR` | `.` | Output directory |
| `--max-scale METRES` | 95th percentile | Ceiling of the colour scale |

#### Python API

```python
from gpx_analyst.compare_gpx import parse_gpx, compare_tracks, visualize

reference  = parse_gpx("reference.gpx")
comparison = parse_gpx("comparison.gpx")
result     = compare_tracks(reference, comparison)

map_path, plot_path = visualize(result, output_dir="./output")

print(f"Max deviation:  {result.max_deviation:.1f} m")
print(f"Within 10 m:    {result.within_threshold(10)*100:.0f} %")
```

#### Outputs

- **`comparison_map.html`** — Interactive Folium map with dashed reference track, colour-coded comparison track (green → yellow → red by deviation), colour-bar legend, statistics panel, layer controls, and per-segment deviation tooltips.
- **`comparison_plot.png`** — Static matplotlib chart of deviation (m) vs. cumulative distance (km), continuously colour-coded.

---

### `gpx_analyst.riding_together` — Co-riding Detection

Determines whether multiple cyclists were riding in close proximity, and for how long. Intended for rule-compliance review in unsupported ultra-cycling events.

#### CLI

```bash
riding-together rider_a.gpx rider_b.gpx rider_c.gpx -o ./output
gpx-analyst riding-together --input-dir ./riders -o ./output
```

| Flag | Default | Description |
|---|---|---|
| `--proximity-threshold METRES` | 100 | Max separation to count as "together" |
| `--min-duration-s SECONDS` | 300 | Minimum epoch length to report |
| `--grid-interval-s SECONDS` | 10 | Resampling resolution |

#### Python API

```python
from gpx_analyst.core.parser import parse_gpx
from gpx_analyst.riding_together.analyzer import analyze

tracks = [parse_gpx(f) for f in gpx_files]
labels = [f.stem for f in gpx_files]

result = analyze(tracks, labels, proximity_threshold_m=100.0, min_duration_s=300.0)

for epoch in result.epochs:
    print(f"{epoch.rider_a} & {epoch.rider_b}: {epoch.duration_min:.1f} min "
          f"(mean sep {epoch.mean_dist_m:.0f} m)")
```

#### Algorithm Summary

1. Parse and validate all tracks; drop untimstamped points.
2. Find the common time window across all riders.
3. Resample every track to a shared 10-second grid via `core.geo.interpolate_track`.
4. Compute pairwise Haversine distances at every grid step.
5. Detect contiguous runs where distance < threshold for ≥ `min_duration_s`.
6. Suppress false positives from start/finish corrals (first and last 30 min excluded).
7. Report `ProximityEpoch` records with duration, mean/min separation, centroid, and lead-rider heuristic.

#### Outputs

- Per-pair proximity epochs with duration, mean/min separation, and map centroid.
- Interactive Folium map with co-riding segments highlighted.
- Timeline chart showing which pairs were close at each hour of the race.

---

### `gpx_analyst.suspicious_stops` — Unsupported Resupply Detection

Analyses stationary periods in GPX tracks for characteristics of an illegal vehicle resupply stop in unsupported ultra-endurance events.

#### CLI

```bash
suspicious-stops rider_a.gpx rider_b.gpx -o ./output
gpx-analyst suspicious-stops --input-dir ./riders -o ./output
```

| Flag | Default | Description |
|---|---|---|
| `--min-stop-duration-s SECONDS` | 600 | Minimum stop length to analyse |
| `--poi-radius-m METRES` | 50 | Radius for OSM POI cross-reference |
| `--coincidence-radius-m METRES` | 200 | Radius for multi-rider coincidence check |
| `--osm-cache-dir DIR` | `.osm_cache` | Cache directory for Overpass API responses |

#### Python API

```python
from gpx_analyst.core.parser import parse_gpx
from gpx_analyst.suspicious_stops.analyzer import analyze

tracks = [parse_gpx(f) for f in gpx_files]
labels = [f.stem for f in gpx_files]

result = analyze(tracks, labels, poi_radius_m=50.0)

for rider, stops in result.stops_by_rider.items():
    for stop in stops:
        print(f"{rider} — {stop.classification} (score {stop.score:.2f}) "
              f"at {stop.epoch.lat:.4f}, {stop.epoch.lon:.4f} "
              f"for {stop.epoch.duration_s/60:.0f} min")
```

#### Scoring Model

Each stop receives a suspicion score 0.0 – 1.0 from five independent signals:

| Signal | Weight | Description |
|---|---|---|
| POI match | 0.35 | Stop centroid within 50 m of vehicle-accessible OSM POI |
| Duration | 0.20 | Stops > 30 min score higher; > 60 min scores maximum |
| Departure jerk | 0.20 | Unusually sharp acceleration on departure (vehicle hand-off pattern) |
| Racing hours | 0.15 | Stops during daylight hours score higher than night stops |
| Multi-rider coincidence | 0.10 | Another rider stops at the same location within 15 min |

| Score | Classification |
|---|---|
| 0.00 – 0.29 | Normal |
| 0.30 – 0.59 | Noteworthy |
| 0.60 – 0.79 | Suspicious |
| 0.80 – 1.00 | Highly suspicious |

OSM POI queries are cached to a local JSON file to minimise Overpass API calls.

---

### `gpx_analyst.mutant_performance` — Sleep Debt vs Power Output

Quantifies how a rider's power output degrades as sleep deprivation accumulates over a multi-day ultra-cycling event.

#### CLI

```bash
mutant-perf rider.gpx -o ./output
gpx-analyst mutant-perf rider.gpx -o ./output
```

| Flag | Default | Description |
|---|---|---|
| `--min-sleep-min MINUTES` | 30 | Minimum stop to classify as sleep |
| `--np-window-min MINUTES` | 30 | Window for normalised power computation |
| `--mass-kg KG` | 80.0 | Rider + bike mass (for power estimation) |

#### Python API

```python
from gpx_analyst.core.parser import parse_gpx
from gpx_analyst.mutant_performance.analyzer import analyze

track = parse_gpx("rider.gpx")
result = analyze(track, label="Rider A")

print(f"Pearson r (sleep debt vs NP): {result.correlation.pearson_r:.3f} "
      f"(p={result.correlation.pearson_p:.4f})")
print(f"Performance breakpoint at {result.correlation.breakpoint_debt_h:.0f} h sleep debt")

for phase, power in result.power_by_phase.items():
    print(f"  {phase:10s}  {power:.0f} W" if power else f"  {phase:10s}  —")
```

#### Algorithm Summary

1. **Sleep detection** — stationary periods ≥ 30 min within 18:00–10:00 (or > 90 min any time) classified as sleep; consecutive events within 20 min merged.
2. **Sleep debt accumulation** — $D(t) = (t - t_0) - \sum_i \min(s_i, 8\text{ h})$, clamped to $[0, \infty)$.
3. **Power series** — use GPX power extension if present, otherwise estimate via `core.power`; apply 60 s rolling mean; compute 30-min normalised power (NP) windows.
4. **Correlation** — Pearson r, Spearman ρ, rolling 4-hour Pearson, piecewise-linear breakpoint detection.
5. **Performance phases** — classify each hour as `fresh` / `fatigued` / `depleted` / `zombie` / `sleeping`; report mean NP and speed per phase.

#### Outputs

- Dual-axis time-series plot: normalised power (left) and sleep debt (right).
- Scatter plot of power vs sleep debt with regression line and confidence interval.

---

### `gpx_analyst.drafting` — Draft-Zone Likelihood Detection

Determines whether riders were travelling in each other's aerodynamic slipstream using a probabilistic geometric model that accounts for consumer GPS accuracy.

#### CLI

```bash
drafting rider_a.gpx rider_b.gpx -o ./output
gpx-analyst drafting --input-dir ./riders -o ./output
```

| Flag | Default | Description |
|---|---|---|
| `--d-max-m METRES` | 25 | Max total separation for draft zone |
| `--w-max-m METRES` | 1.5 | Max lateral offset for draft zone |
| `--min-speed-ms MS` | 5.0 | Min speed (m/s) for drafting to be meaningful |
| `--gps-sigma-m METRES` | 5.0 | GPS horizontal error 1σ |
| `--min-draft-duration-s SECONDS` | 60 | Minimum epoch length to report |

#### Python API

```python
from gpx_analyst.core.parser import parse_gpx
from gpx_analyst.drafting.analyzer import analyze

tracks = [parse_gpx(f) for f in gpx_files]
labels = [f.stem for f in gpx_files]

result = analyze(tracks, labels, d_max_m=25.0, w_max_m=1.5)

for epoch in result.epochs:
    print(f"{epoch.follower} drafted {epoch.lead_rider}: "
          f"{epoch.duration_s:.0f} s "
          f"(p={epoch.mean_probability:.2f}, "
          f"Δlateral={epoch.mean_lateral_m:.1f} m)")
```

#### Algorithm Summary

1. Resample all tracks to a common 5-second grid.
2. Smooth GPS headings using a Gaussian-weighted circular mean over a short forward window.
3. For each pair at each timestep, decompose the displacement vector into components parallel and perpendicular to the lead rider's heading.
4. Apply hard thresholds on total distance, lateral offset, and minimum speed.
5. Model the true lateral offset as a Gaussian (combining two GPS error terms in quadrature) and compute:

$$p_t = \Phi\!\left(\frac{w_{\max} - d_{\perp}}{\sigma_{\text{GPS}}\sqrt{2}}\right)$$

6. Aggregate timesteps where $p_t > 0.5$ into draft epochs of ≥ 60 s.
7. Optionally validate against power data: genuine drafters show anomalously low NP for their speed.

#### Outputs

- Interactive Folium map with draft epochs highlighted per pair.
- Per-pair probability timeline over race time.
- Optional power-validation report showing power deficit (%) during draft epochs.

---

## Batch Mode

`BatchRunner` in `gpx_analyst.batch` runs all applicable analyses in parallel using `ProcessPoolExecutor` and renders a combined HTML report via Jinja2.

```python
from pathlib import Path
from gpx_analyst.batch import BatchRunner

runner = BatchRunner(
    paths=list(Path("riders").glob("*.gpx")),
    output_dir=Path("race_report"),
    workers=4,
)
report_path = runner.run_all()
print(f"Report: {report_path}")
```

Dispatch rules:
- `suspicious_stops` and `mutant_performance` run on every individual file.
- `riding_together` and `drafting` run on the full set when ≥ 2 files are provided.
- `compare_gpx` runs when exactly 2 files are provided.

---

## Dependencies

| Package | Version | Used for |
|---|---|---|
| `gpxpy` | ≥ 1.5.0 | GPX file parsing |
| `numpy` | ≥ 1.24 | Array operations throughout |
| `matplotlib` | ≥ 3.7 | Static plots |
| `folium` | ≥ 0.15 | Interactive HTML maps |
| `branca` | ≥ 0.7 | Colour maps and legends for Folium |
| `pandas` | ≥ 2.0 | Time-series alignment and rolling statistics |
| `scipy` | ≥ 1.11 | Spline interpolation, statistics, signal processing |
| `statsmodels` | ≥ 0.14 | Rolling OLS, confidence intervals |
| `osmnx` | ≥ 1.9 | Overpass API queries for POI data |
| `jinja2` | ≥ 3.1 | Combined report rendering |
| `tqdm` | ≥ 4.0 | Progress bars in batch mode |
| `scikit-learn` _(optional)_ | ≥ 1.3 | Install with `pip install -e "[full]"` |
- Shaded threshold zones: green (< 5 m), yellow (5–15 m), red (> 15 m)
- Summary statistics annotation at the top of the chart

---

## How deviation is calculated

For every point $P_i$ in the comparison track the algorithm finds its shortest distance to the reference **polyline** (not just the nearest point):

$$d_i = \min_j \left\| P_i - \left( A_j + \text{clip}(t,\,0,\,1)\cdot(B_j - A_j) \right) \right\|, \quad t = \frac{(P_i - A_j)\cdot(B_j - A_j)}{\|B_j - A_j\|^2}$$

Coordinates are first projected to approximate metres using an equirectangular projection centred on the tracks' centroid, accurate to < 0.5 % for extents up to ~200 km. Computation is batched so large tracks (tens of thousands of points) run without exhausting memory.

---

## Project structure

```
compareGPXtracks/
├── compare_gpx/
│   ├── __init__.py     # public API re-exports
│   ├── parser.py       # parse_gpx() → List[TrackPoint]
│   ├── comparator.py   # compare_tracks() → ComparisonResult
│   ├── visualizer.py   # visualize_map(), visualize_plot(), visualize()
│   ├── cli.py          # argparse entry point
│   └── __main__.py     # enables `python -m compare_gpx`
├── requirements.txt
└── pyproject.toml
```
