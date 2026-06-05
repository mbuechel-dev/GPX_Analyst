# `gpx_analyst.drafting` — Draft-Zone Likelihood Detection

Determines whether riders were drafting (riding in each other's aerodynamic
slipstream) by analysing the relative geometry of their GPS trajectories.

---

## Purpose

In cycling, riding behind another rider at close range provides a
significant aerodynamic advantage (typically 20–30 % reduction in
aerodynamic drag).  In unsupported or non-drafting ultra-cycling events,
intentional drafting is prohibited.

This module answers: **"Was rider B travelling in rider A's draft zone,
and for how long?"**  It accounts for the inherent imprecision of consumer
GPS (±5 m typical horizontal error) by computing a probabilistic likelihood
rather than a binary classification.

---

## Inputs

- Two or more GPX files with timestamps.
- All files must contain timestamps.

## Outputs

- `DraftingResult` with per-pair `DraftEpoch` list and likelihood statistics.
- An interactive Folium map with draft epochs highlighted.
- A per-pair timeline showing drafting probability over race time.
- An optional power-validation report (if power data is available).

---

## Algorithm

### Step 1 — Time-align all tracks (`interpolator.py`)

Resample every track to a common 5-second grid using
`gpx_analyst.core.geo.interpolate_track`.

**Why 5 seconds?** Consumer GPS typically records every 1–5 s.  A 5-second
grid provides adequate spatial resolution for heading computation while
keeping the computation tractable.  At 40 km/h, 5 seconds = ~55 m — fine
enough to resolve draft-zone geometry.

### Step 2 — Smooth headings

Raw GPS bearings are extremely noisy at low speeds and during turns.
For each rider at each timestep, compute a **Gaussian-weighted smoothed
heading** over a short forward window:

1. For the 5 points centred at $t$ (i.e. $t-10s$ to $t+10s$), compute
   the bearing from each point to the next.
2. Weight bearings by a Gaussian kernel (σ = 1.5 steps).
3. Use circular mean to average bearings (to handle the 0°/360° wrap).

This suppresses single-point GPS outliers while preserving genuine
direction changes.

### Step 3 — Draft zone geometry test

For each pair $(A, B)$ at each timestep $t$:

Let:
- $\vec{p}_A$, $\vec{p}_B$ — projected positions in metres (via `core.geo.to_meters`)
- $\hat{h}_A$ — unit heading vector of rider A
- $\vec{v}_{AB} = \vec{p}_B - \vec{p}_A$ — displacement from A to B

Decompose $\vec{v}_{AB}$ into components parallel and perpendicular to $\hat{h}_A$:

$$d_{\parallel} = \vec{v}_{AB} \cdot \hat{h}_A \quad (\text{positive = B is ahead of A})$$
$$d_{\perp}   = |\vec{v}_{AB} \times \hat{h}_A| \quad (\text{lateral offset})$$
$$d             = |\vec{v}_{AB}| \quad (\text{total distance})$$

**Nominal draft zone conditions:**
- $d < d_{\max}$ (default 25 m) — close enough to be in slipstream
- $d_{\parallel} < 0$ — B is **behind** A (not ahead)
- $d_{\perp} < w_{\max}$ (default 1.5 m) — B is directly behind, not side-by-side
- Both riders' speeds ≥ `min_speed_ms` (default 5 m/s ≈ 18 km/h) — no
  drafting benefit at walking pace

### Step 4 — Probabilistic likelihood

GPS horizontal error is approximately Gaussian with σ ≈ 5 m (consumer
receivers under open sky; worse under tree cover or in canyons).

The true lateral offset $d_{\perp}^*$ given observed $d_{\perp}$ is modelled
as:

$$d_{\perp}^* \sim \mathcal{N}(d_{\perp},\ \sigma_{\text{GPS}}^2 + \sigma_{\text{GPS}}^2)$$

(two independent GPS errors add in quadrature, giving $\sigma_{\text{combined}} = \sigma_{\text{GPS}}\sqrt{2}$).

The per-timestep drafting probability is:

$$p_t = P(d_{\perp}^* < w_{\max}) = \Phi\!\left(\frac{w_{\max} - d_{\perp}}{\sigma_{\text{combined}}}\right)$$

where $\Phi$ is the standard normal CDF.  This gives a smooth probability
that accounts for GPS uncertainty: a rider observed at $d_{\perp} = 2$ m
with σ = 5 m still has a meaningful drafting probability; a rider at
$d_{\perp} = 10$ m has near-zero probability.

All other conditions ($d$, $d_{\parallel}$, speed) are applied as hard thresholds
before computing $p_t$.  Points failing hard thresholds receive $p_t = 0$.

### Step 5 — Epoch aggregation

A **draft epoch** is a contiguous run of timesteps where $p_t > 0.5$ for
at least `min_draft_duration_s` (default 60 s).

For each epoch record:
- `start_time`, `end_time`, `duration_s`
- `mean_probability` = mean($p_t$) over the epoch
- `mean_distance_m`, `mean_lateral_m`
- `lead_rider`, `follower`
- `mean_speed_ms`

### Step 6 — Power validation (optional)

If power data is available (or estimated), for each draft epoch compute
the follower's **Normalised Power** and compare against their median NP
at the same speed range from non-drafting segments.

A genuine drafter will show anomalously low NP for their speed — because
the aerodynamic load is reduced by 20–30 %.  This is an independent
physical signal that strengthens the draft classification.

Report the power deficit (%):

$$\text{power\_deficit} = \frac{\text{NP}_{\text{solo baseline}} - \text{NP}_{\text{epoch}}}{\text{NP}_{\text{solo baseline}}} \times 100$$

---

## Configurable Parameters

| Parameter | Default | Description |
|---|---|---|
| `grid_interval_s` | 5 | Resampling resolution (seconds) |
| `d_max_m` | 25 | Max total separation for draft zone |
| `w_max_m` | 1.5 | Max lateral offset for draft zone |
| `min_speed_ms` | 5.0 | Min speed for drafting to be meaningful |
| `gps_sigma_m` | 5.0 | GPS horizontal error 1σ (metres) |
| `prob_threshold` | 0.5 | Minimum per-timestep probability to count |
| `min_draft_duration_s` | 60 | Minimum epoch length to report |

---

## `interpolator.py` — Track Alignment

A dedicated module for multi-track time alignment, wrapping
`gpx_analyst.core.geo.interpolate_track` with:
- Automatic detection and warning of data gaps > 5 min.
- Optional Kalman filter smoothing of positions before interpolation
  (reduces GPS jitter for low-speed segments where position noise is
  disproportionately large relative to movement).
- Batch processing of N tracks to a common grid in a single call.

---

## Key Dependencies

| Package | Used for |
|---|---|
| `numpy` | Heading computation, distance decomposition |
| `scipy.stats` | Normal CDF for probability model |
| `scipy.signal` | Gaussian kernel for heading smoothing |
| `pandas` | Time-series operations |
| `folium` | Interactive map |
| `matplotlib` | Probability timeline chart |
| `gpx_analyst.core.geo` | `to_meters`, `interpolate_track` |

---

## Limitations & Future Work

- The 1.5 m lateral threshold is very tight relative to GPS accuracy (σ ≈ 5 m).
  The probabilistic model accounts for this, but it means most draft
  classifications will have $p_t \in [0.3, 0.7]$ rather than approaching 1.0.
  High-confidence detections require unusually good GPS conditions.
- The model treats each timestep independently.  A temporal smoothing
  prior (Hidden Markov Model: states = drafting / not-drafting) would
  better handle the bursty nature of GPS errors and give more stable epoch
  boundaries.  This is the recommended next step for production use.
- Drafting on descents (high speed, same trajectory) could be mis-classified
  as close proximity even if riders are 30 m apart.  The $d_{\max}$ = 25 m
  threshold helps, but a descent-aware speed correction would be cleaner.
- Does not yet handle three-rider trains (A drafts B who drafts C).
  Extend by computing the draft zone relative to the group centroid.
