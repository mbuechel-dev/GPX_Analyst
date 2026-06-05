"""Sleep period detection and sleep-debt accumulation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List

from gpx_analyst.core.parser import TrackPoint


@dataclass
class SleepPeriod:
    """A classified sleep epoch."""
    start_time: datetime
    end_time: datetime
    duration_min: float
    lat: float
    lon: float


@dataclass
class SleepSchedule:
    """Full sleep schedule derived from a single rider's track."""
    periods: List[SleepPeriod]
    race_start: datetime
    race_end: datetime

    def debt_at(self, t: datetime, max_credit_h: float = 8.0) -> float:
        """
        Return accumulated sleep debt in hours at time *t*.

        D(t) = (t - race_start) - sum of min(sleep_dur, max_credit_h)
               for all sleeps ending before t

        Clamped to [0, ∞).
        """
        raise NotImplementedError(
            "SleepSchedule.debt_at is not yet implemented. "
            "See gpx_analyst/mutant_performance/README.md."
        )


def detect_sleep_periods(
    track: List[TrackPoint],
    min_sleep_min: float = 30.0,
    sleep_window_start_h: int = 18,
    sleep_window_end_h: int = 10,
    min_wake_h: float = 4.0,
    merge_gap_min: float = 20.0,
) -> SleepSchedule:
    """
    Identify sleep periods in *track* and return a SleepSchedule.

    Parameters
    ----------
    track                : parsed track with timestamps
    min_sleep_min        : minimum stop duration to classify as sleep
    sleep_window_start_h : local hour when the sleep window opens (18 = 6 PM)
    sleep_window_end_h   : local hour when the sleep window closes (10 = 10 AM)
    min_wake_h           : minimum awake time before a new sleep is recorded
    merge_gap_min        : merge consecutive sleeps separated by less than this

    Returns
    -------
    SleepSchedule

    Algorithm
    ---------
    1. Call core.geo.detect_stops to get all stationary periods ≥ min_sleep_min.
    2. Filter to those within the sleep window OR longer than 90 min.
    3. Enforce minimum wake gap between consecutive sleeps.
    4. Merge sleeps separated by < merge_gap_min.
    5. Return SleepSchedule with the resulting list of SleepPeriod objects.

    See README.md for full details.
    """
    raise NotImplementedError(
        "detect_sleep_periods is not yet implemented. "
        "See gpx_analyst/mutant_performance/README.md."
    )
