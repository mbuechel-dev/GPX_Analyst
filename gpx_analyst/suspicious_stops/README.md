# `gpx_analyst.suspicious_stops` — Unsupported Resupply Detection

Analyses GPX tracks from unsupported ultra-cycling events for stationary
periods that exhibit characteristics of an illegal car resupply stop.

---

## Purpose

In unsupported ultra-endurance events (e.g. Transcontinental Race, GBDURO,
Traka Adventure) riders must be fully self-supported — they cannot receive
outside assistance, food, or equipment from a support vehicle.  A common
form of cheating is stopping in a car park or lay-by where a support car
meets the rider.

This module flags stops that are:
1. Longer than expected for a legitimate nutrition/mechanical stop.
2. Located near known vehicle infrastructure (parking lots, petrol stations,
   rest areas, logistics pick-up points).
3. Optionally: coincide with another rider's stop at the same location.

---

## Inputs

- One or more GPX files (one per rider under scrutiny).
- Optional: a bounding box for OSM queries (auto-derived if not provided).
- Optional: a list of designated sleep/service checkpoints to exclude.

## Outputs

- `SuspiciousStopsResult` containing per-rider, per-stop assessments.
- An interactive map showing all stops colour-coded by suspicion score.
- A CSV/table report suitable for race jury review.

---

## Algorithm

### Step 1 — Detect all stationary periods

Call `gpx_analyst.core.geo.detect_stops(track, speed_threshold_ms=1.0,
min_duration_s=600)` to get all stops ≥ 10 minutes.

For analysis purposes, stops < 2 min are ignored entirely (brief traffic
lights, photo stops).  Stops 2–10 min are noted but not flagged as suspicious.

### Step 2 — Query OpenStreetMap for vehicle infrastructure POIs

For each stop centroid, query the Overpass API (via `osmnx`) for any of
the following within a configurable radius (default 50 m):

| OSM tag | Meaning |
|---|---|
| `amenity=parking` | Public / private car park |
| `amenity=parking_space` | Individual marked space |
| `amenity=fuel` | Petrol station |
| `highway=rest_area` | Motorway rest area |
| `highway=services` | Full motorway services |
| `amenity=parcel_locker` | Package pick-up locker (DHL, InPost, etc.) |
| `amenity=post_box` | Post box (package drop-off) |
| `shop=convenience` | Convenience store with car access |

A single OSM query is made per bounding box (not per stop) to minimise
API calls, then results are cached locally to a JSON file so re-runs are
fast and respectful of the Overpass rate limit.

### Step 3 — Score each stop

Each stop receives a **suspicion score** from 0.0 to 1.0 built from
multiple independent signals:

| Signal | Weight | Description |
|---|---|---|
| POI match | 0.35 | Is the stop centroid within 50 m of a vehicle-accessible POI? |
| Duration | 0.20 | Stops > 30 min score higher; > 60 min score maximum |
| Departure jerk | 0.20 | Unusually sharp speed-up on departure (vehicle hand-off) |
| Racing-hours | 0.15 | Stops during daylight racing hours score higher than night stops |
| Multi-rider coincidence | 0.10 | Do other riders stop at the same place within 15 min? |

**Departure jerk** is the rate of change of acceleration on the first
60 seconds after the stop ends.  A legitimate nutrition stop shows a
gradual ramp-up; a vehicle hand-off shows a sharp spike (rider accelerated
while still inside or immediately alongside the vehicle).

Concretely: compute speed in 5-second bins for the 2 minutes after stop
end.  Fit a line to the first 30 s; the slope is the "departure acceleration".
Compare against the rider's median departure acceleration from all stops.
A z-score > 2.0 contributes to the jerk signal.

### Step 4 — Multi-rider coincidence (optional, multi-file mode)

If multiple GPX files are provided, for each suspicious stop check whether
any other rider also stopped within `coincidence_radius_m` (default 200 m)
and `coincidence_window_min` (default 15 min) of the same time.  Such
coincidences between riders who are otherwise NOT classified as "riding
together" (see `riding_together` module) are strong anomaly signals.

### Step 5 — Exclude known checkpoints

If a list of designated service checkpoints (lat/lon + time windows) is
provided (e.g. from the race roadbook), stops within 500 m of a checkpoint
during its service window are automatically excluded from scoring.

---

## Suspicion Thresholds

| Score | Classification |
|---|---|
| 0.0 – 0.29 | Normal stop |
| 0.30 – 0.59 | Noteworthy (flag for manual review) |
| 0.60 – 0.79 | Suspicious |
| 0.80 – 1.00 | Highly suspicious |

---

## Configurable Parameters

| Parameter | Default | Description |
|---|---|---|
| `min_stop_duration_s` | 600 | Minimum stop length to analyse (10 min) |
| `poi_radius_m` | 50 | Radius for OSM POI cross-reference |
| `coincidence_radius_m` | 200 | Radius for multi-rider coincidence check |
| `coincidence_window_min` | 15 | Time window for multi-rider coincidence |
| `osm_cache_dir` | `.osm_cache` | Directory for cached Overpass API responses |

---

## Key Dependencies

| Package | Used for |
|---|---|
| `osmnx` | Overpass API queries for POIs |
| `numpy` / `pandas` | Stop scoring computations |
| `folium` | Interactive map output |
| `gpx_analyst.core.geo` | `detect_stops`, `haversine_distance` |

---

## Limitations & Future Work

- OSM data quality varies by country and region.  In rural areas, informal
  parking spots may not be mapped.  Scoring relies on what is in OSM.
- The departure-jerk signal requires high-resolution timestamps (≤ 5 s
  recording interval).  Many consumer GPS devices use adaptive recording
  that coarsens during slow movement — exactly when this signal is needed.
- A future version could cross-reference with mobile cell-tower data or
  Strava segment efforts to independently verify timing.
- Race organisers could supply a GPX-format "safe zone" file (known service
  checkpoints) that this module automatically excludes from scoring.
