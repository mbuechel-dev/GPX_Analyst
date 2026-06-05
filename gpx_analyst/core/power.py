"""Physics-based cycling power estimator.

Used by mutant_performance when a GPX file contains no power extension data,
and by drafting to compute a baseline "solo power" for draft-zone validation.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import numpy as np

from .parser import TrackPoint


@dataclass
class PowerParams:
    """Physical parameters for the power model.  All defaults are reasonable
    averages for an endurance cyclist on a gravel/road bike.

    Attributes
    ----------
    mass_kg         : total system mass (rider + bike + kit), kg
    Cr              : rolling resistance coefficient (dimensionless)
    CdA             : drag area (C_d × frontal area), m²
    rho             : air density, kg/m³  (1.225 at sea level, 20 °C)
    drivetrain_eff  : drivetrain efficiency (fraction); default 0.975
    gravity         : gravitational acceleration, m/s²
    """
    mass_kg: float = 80.0
    Cr: float = 0.004
    CdA: float = 0.32
    rho: float = 1.225
    drivetrain_eff: float = 0.975
    gravity: float = 9.80665


def estimate_power(
    track: List[TrackPoint],
    params: Optional[PowerParams] = None,
    smooth_window_s: float = 60.0,
) -> List[Optional[float]]:
    """
    Estimate mechanical power output (watts) for each point in *track*.

    Requires timestamped points.  Points without timestamps, or the first
    point of the track, receive None.

    The standard cycling power equation is applied per segment:

        P = (F_roll + F_grav + F_aero) × v / η

    where:
        F_roll = m × g × C_r
        F_grav = m × g × sin(θ)        θ = gradient angle
        F_aero = ½ × ρ × CdA × v²
        v      = instantaneous speed (m/s)
        η      = drivetrain efficiency

    Negative power values (descents faster than the rider is pedalling)
    are clamped to 0 — we model mechanical output, not braking.

    A rolling mean over *smooth_window_s* seconds is applied to the raw
    per-segment estimates before returning, to suppress GPS noise.

    Parameters
    ----------
    track          : list of TrackPoint with non-None timestamps
    params         : PowerParams (uses defaults if None)
    smooth_window_s: width of the smoothing window in seconds

    Returns
    -------
    List of Optional[float] of the same length as *track*.
    None for points that cannot be estimated (no timestamp, first point).

    Notes
    -----
    - Gradient is computed as Δele / Δdist (finite difference).
    - Speed is computed from Haversine distance / Δt between consecutive points.
    - The model does not account for wind speed or direction.  If a consistent
      wind correction is desired, pass an adjusted CdA.
    - Altitude data quality has a large impact on gradient accuracy.
      Consider smoothing elevation with a Savitzky-Golay filter beforehand
      (scipy.signal.savgol_filter) for noisy barometric/GPS altitude tracks.

    Algorithm
    ---------
    1. Filter to timestamped points.
    2. For each consecutive pair, compute Δt (s), Δdist (m), speed (m/s),
       gradient (Δele / Δdist), and apply the power equation.
    3. Clamp negative values to 0.
    4. Apply rolling mean over the smoothing window.
    5. Map results back to the original track index, filling None for
       non-timestamped points.
    """
    raise NotImplementedError(
        "estimate_power is not yet implemented. "
        "See gpx_analyst/core/README.md for the algorithm design."
    )
