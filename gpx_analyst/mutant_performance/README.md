# `gpx_analyst.mutant_performance` — Sleep Deprivation vs Power Output

Quantifies how a rider's power output degrades as sleep deprivation
accumulates over a multi-day ultra-cycling event.

The name "mutant performance" is a nod to the phenomenon observed in
sleep-deprived ultra-endurance athletes: their performance becomes
erratic, with unexpected surges and collapses that seem disconnected
from normal physiological models.

---

## Purpose

In multi-day ultra-cycling (e.g. Transcontinental Race, GBDURO 500,
Pan-Celtic Race), riders can stay awake for 36–60+ hours.  Cognitive
and physical performance degrades non-linearly beyond approximately
20–24 hours of wakefulness.

This module answers:
- **When did the rider sleep, and for how long?**
- **How much accumulated sleep debt did the rider carry at each point?**
- **Is there a statistically significant correlation between sleep debt
  and power output (or speed-adjusted power)?**
- **At what sleep-debt threshold did the rider's performance most visibly
  decline?**

---

## Inputs

- One GPX file per rider.
- GPX files with Garmin/Wahoo power extensions are used directly.
- Without power data, power is estimated via `gpx_analyst.core.power`.
- Timestamps are mandatory.

## Outputs

- `MutantPerformanceResult` with sleep schedule, power time-series, and
  correlation statistics.
- A dual-axis time-series plot: power (left axis) and sleep debt (right axis).
- A scatter plot of power vs sleep debt with regression line and
  confidence interval.

---

## Algorithm

### Step 1 — Sleep period detection (`sleep.py`)

A **sleep period** is any stationary period (from `core.geo.detect_stops`)
that meets all of:
1. Duration ≥ `min_sleep_min` (default 30 min).
2. Starts between `sleep_window_start` (default 18:00) and
   `sleep_window_end` (default 10:00 next day) **or** is unusually long
   (> 90 min) regardless of time — extended involuntary stops (mechanical,
   medical) can occur at any hour.
3. The rider's previous "wake period" was at least `min_wake_h` (default 4 h)
   — this prevents counting a brief rest immediately after another sleep.

**Edge case**: Riders sometimes sleep in shifts (15–20 min micro-naps).
Consecutive sleep events within `merge_gap_min` (default 20 min) of each
other are merged into one sleep period.

### Step 2 — Sleep debt accumulation

Let $t_0$ be the race start time.  Sleep debt at time $t$ is:

$$D(t) = (t - t_0) - \sum_{i:\, s_i^{\text{end}} \leq t} \min(s_i^{\text{dur}},\, C_{\max})$$

where:
- $s_i^{\text{dur}}$ is the duration of the $i$-th sleep period (hours)
- $C_{\max}$ = 8 h — a single sleep can reduce debt by at most one full
  night's sleep worth of recovery

The debt $D(t)$ is clamped to $[0, \infty)$ — the rider cannot "bank"
sleep debt below zero.

### Step 3 — Power series

1. If the GPX file contains power extension data, use it directly.
2. Otherwise, call `gpx_analyst.core.power.estimate_power(track, params)`.
3. Apply a 60-second rolling mean to suppress GPS noise.
4. Compute **normalised power** (NP) over 30-minute windows using the
   standard formula:
   $$\text{NP}_{30} = \left(\frac{1}{N}\sum_{i=1}^{N} p_i^4\right)^{1/4}$$
   where $p_i$ are the 30-second rolling-mean power values within the window.

### Step 4 — Correlation analysis

For each 30-minute window centred at time $t$:
- $D_t$ = sleep debt at window midpoint (hours)
- $P_t$ = NP for the window (watts)

Compute:
- **Pearson r** and two-sided p-value between $D$ and $P$ series.
- **Spearman ρ** (rank correlation, robust to outliers).
- **Rolling Pearson** over a 4-hour sliding window to show how the
  correlation evolves during the race.
- **Breakpoint detection**: find the sleep-debt threshold at which power
  drops most sharply.  Use a simple piecewise linear fit (two segments)
  minimising residual sum of squares — sweep breakpoints from 10 h to 40 h
  in 1-hour increments.

### Step 5 — Performance phases

Classify each hour of the race into one of:
- `sleeping` — rider is in a sleep period
- `fresh` — $D < 10$ h
- `fatigued` — $10 \leq D < 20$ h
- `depleted` — $20 \leq D < 30$ h
- `zombie` — $D \geq 30$ h

Report mean NP and mean speed for each phase.

---

## Configurable Parameters

| Parameter | Default | Description |
|---|---|---|
| `min_sleep_min` | 30 | Minimum stop to classify as sleep (minutes) |
| `sleep_window_start` | 18 | Hour of day when sleep window opens |
| `sleep_window_end` | 10 | Hour of day when sleep window closes |
| `max_sleep_credit_h` | 8 | Maximum sleep-debt reduction per sleep period |
| `smooth_window_s` | 60 | Rolling mean window for power smoothing |
| `np_window_min` | 30 | Window for normalised power computation |
| `correlation_window_h` | 4 | Rolling window for time-varying Pearson r |

---

## Key Dependencies

| Package | Used for |
|---|---|
| `numpy` / `pandas` | Time-series operations |
| `scipy.stats` | Pearson, Spearman correlation |
| `statsmodels` | Rolling OLS, confidence intervals |
| `matplotlib` | Dual-axis plot, scatter plot |
| `gpx_analyst.core.power` | Power estimation without extension data |
| `gpx_analyst.core.geo` | `detect_stops` |

---

## Limitations & Future Work

- Without barometric altitude data, estimated power is sensitive to GPS
  elevation noise.  Smoothing elevation before estimation is strongly
  recommended (Savitzky-Golay, window ≈ 60 s).
- Sleep classification relies purely on GPS speed.  A bivvy stop in a
  field with no OSM trace will be classified correctly; a rider who stops
  for 45 min in an energy store but remains awake will be mis-classified.
  Heart-rate data (if available in the GPX extension) would resolve this.
- The breakpoint detection is a brute-force sweep.  For production use,
  replace with `ruptures` library (change-point detection).
