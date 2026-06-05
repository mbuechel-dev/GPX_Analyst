# `gpx_analyst.core` — Shared Utilities

The `core` subpackage provides the data model and geospatial / physical
utilities that are shared across every analysis subpackage.  No analysis
logic lives here — only building blocks.

---

## Data Model

### `TrackPoint`

```python
@dataclass
class TrackPoint:
    lat:   float
    lon:   float
    ele:   float
    time:  Optional[datetime]
    power: Optional[float]      # watts — from GPX extension or estimated
```

`power` is `None` unless:
- The GPX file contains a Garmin/Wahoo power extension
  (`<gpxtpx:PowerInWatts>` or `<power>`), **or**
- `core.power.estimate_power()` has been called on the track.

All subpackages operate on `List[TrackPoint]`.

---

## Modules

### `parser.py` — `parse_gpx(path) → List[TrackPoint]`

Wraps `gpxpy`.  Tries tracks → routes → waypoints in order.  Reads power
extensions when present.  Raises `ValueError` on empty files.

### `geo.py` — Geospatial helpers

| Function | Purpose |
|---|---|
| `to_meters(lats, lons, lat0, lon0)` | Equirectangular projection to (x, y) metres |
| `haversine_distance(lat1, lon1, lat2, lon2)` | Great-circle distance in metres |
| `min_dist_to_polyline(pts, starts, ends, batch)` | Point-to-polyline distance (used by `compare_gpx`) |
| `detect_stops(track, ...)` | Identify stationary epochs → `List[StopEpoch]` |
| `interpolate_track(track, target_times, method)` | Resample track to arbitrary timestamps |

#### `detect_stops` algorithm

1. Filter to timestamped points; compute per-segment speeds via Haversine.
2. Label each point stationary if speed < `speed_threshold_ms` (default 1 m/s).
3. Group consecutive stationary points into candidate epochs.
4. Discard epochs shorter than `min_duration_s` (default 600 s / 10 min).
5. Return `StopEpoch(start_time, end_time, lat, lon, duration_s)` objects.

#### `interpolate_track` algorithm

1. Convert `datetime` timestamps to float seconds since Unix epoch.
2. Separate lat, lon, ele into three 1-D arrays.
3. **linear**: use `numpy.interp` independently per channel.
4. **cubic**: use `scipy.interpolate.CubicSpline` independently per channel.
5. Clamp output to the source track's time range (no extrapolation).
6. Flag interpolated points that span a gap > 5 min with `ele = float('nan')`.

### `power.py` — `estimate_power(track, params, smooth_window_s) → List[Optional[float]]`

Standard cycling power equation:

$$P = \frac{1}{\eta}\left[\left(m g C_r + m g \sin\theta\right)v + \frac{1}{2}\rho\, C_{dA}\, v^3\right]$$

where:
- $m$ = total system mass (kg), default 80
- $g$ = 9.80665 m/s²
- $C_r$ = rolling resistance coefficient, default 0.004
- $\theta$ = gradient angle = arctan(Δele / Δdist)
- $v$ = speed (m/s) from Haversine distance / Δt
- $\rho$ = air density (kg/m³), default 1.225
- $C_{dA}$ = drag area (m²), default 0.32
- $\eta$ = drivetrain efficiency, default 0.975

Negative values (free-wheel descents) are clamped to 0.
A rolling mean over `smooth_window_s` (default 60 s) suppresses GPS noise.

**Implementation note**: GPS elevation data is often noisy enough to make
raw gradient estimates unusable.  Before calling `estimate_power`, consider
smoothing elevation with `scipy.signal.savgol_filter(ele, window, polyorder=3)`.

---

## Dependencies

| Package | Used for |
|---|---|
| `gpxpy` | GPX file parsing |
| `numpy` | Array operations |
| `scipy` | CubicSpline interpolation (optional path in `interpolate_track`) |
