# `gpx_analyst.riding_together` — Co-riding Detection

Determines whether multiple cyclists were riding together by analysing the
spatial and temporal proximity of their GPS tracks.

---

## Purpose

In ultra-cycling events, riders are allowed to share the road but racing
rules typically prohibit intentional pacing (riding together in a way that
gives a competitive advantage). This module answers: **"Were these riders
travelling together, and for how long?"**

It produces a per-pair report of co-riding epochs with duration, mean
separation distance, and a map overlay showing where the proximity occurred.

---

## Inputs

- Two or more GPX files, each representing one rider.
- All files **must contain timestamps** (`<time>` in each `<trkpt>`).

## Outputs

- `RidingTogetherResult` dataclass containing:
  - A list of `ProximityEpoch` per rider pair
  - Summary statistics (total co-riding time, % of each rider's race)
- An interactive Folium map with co-riding segments highlighted
- A timeline chart showing which pairs were close at each hour of the race

---

## Algorithm

### Step 1 — Parse and validate

Load each GPX file with `gpx_analyst.core.parser.parse_gpx`.  Drop points
without timestamps.  Warn (do not raise) if any track has fewer than 10
timestamped points.

### Step 2 — Find the common time window

```
t_start = max(track.first_time for track in tracks)
t_end   = min(track.last_time  for track in tracks)
```

If `t_end - t_start < min_overlap` (default 30 min) the pair cannot be
analysed and a warning is issued.

### Step 3 — Resample to a shared time grid

Call `gpx_analyst.core.geo.interpolate_track(track, target_times)` to
bring every rider onto a common 10-second grid spanning `[t_start, t_end]`.

**Why 10 seconds?** Consumer GPS devices typically record every 1–5 seconds.
A 10-second grid is fine enough to capture close proximity while being
cheap to compute for long events (24 h = 8 640 grid points).

### Step 4 — Compute pairwise distances

For each pair `(i, j)` of riders and each grid timestamp `t`:

```
d(t) = haversine_distance(lat_i(t), lon_i(t), lat_j(t), lon_j(t))
```

This gives a `(T,)` distance time-series per pair.

### Step 5 — Detect proximity epochs

A **proximity epoch** is a contiguous run of time steps where
`d(t) < proximity_threshold_m` (default 100 m) for at least
`min_duration_s` seconds (default 300 s / 5 min).

Short proximity bursts at start/finish corrals produce false positives.
These are suppressed by excluding the first and last 30 min of the
common time window from epoch detection.

### Step 6 — Epoch statistics

For each epoch record:
- `start_time`, `end_time`, `duration_min`
- `mean_dist_m`, `min_dist_m`
- `centroid_lat`, `centroid_lon` (mean of both riders' positions)
- `lead_rider` (heuristic: the one with lower average power during the epoch,
  or the one furthest ahead in the direction of travel if power is unavailable)

### Step 7 — Summary per pair

```
total_together_min  = sum(epoch.duration_min)
pct_of_race_A       = total_together_min / race_duration_A * 100
pct_of_race_B       = total_together_min / race_duration_B * 100
```

---

## Configurable Parameters

| Parameter | Default | Description |
|---|---|---|
| `grid_interval_s` | 10 | Resampling grid resolution (seconds) |
| `proximity_threshold_m` | 100 | Max separation to count as "together" (metres) |
| `min_duration_s` | 300 | Minimum epoch length to report (seconds) |
| `corral_exclusion_min` | 30 | Ignore proximity within this many minutes of start/end |

---

## Key Dependencies

| Package | Used for |
|---|---|
| `numpy` | Distance array operations |
| `pandas` | Time-series alignment and rolling statistics |
| `folium` | Interactive map output |
| `matplotlib` | Timeline chart |
| `gpx_analyst.core.geo` | `haversine_distance`, `interpolate_track` |

---

## Limitations & Future Work

- Currently uses simple Haversine distance.  For densely forested or hilly
  terrain this may mis-classify adjacent switchbacks as proximity.  A future
  version could project onto the route polyline and use along-track distance.
- "Lead rider" detection is heuristic.  A cleaner approach would compute the
  instantaneous heading of the pair and project positions onto that heading.
- Does not yet account for riders who briefly diverge (e.g. a quick nature
  stop) and then rejoin — these are currently split into two separate epochs.
  A future version could merge epochs with a gap < `merge_gap_s`.
