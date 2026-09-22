"""Domain logic for gate presence and temporal occupancy intervals.

Research Basis:
- Zoutendijk & Mitici (2021): Discretization of the 24-hour operational day into
  5-minute time slots (288 slots per day) for flight-to-gate assignment (FGAP).
- Operational Half-Open Intervals: Occupancy is represented as [T_start, T_end),
  ensuring adjacent turnaround handoffs (e.g. flight 1 leaves at 10:30, flight 2 arrives at 10:30)
  do not register a false positive conflict.
"""

import math
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import List, Optional, Set, Tuple


def ensure_utc(dt: datetime) -> datetime:
    """Ensure datetime is timezone-aware UTC per GEMINI_BACKEND.md Section 14."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


@dataclass(frozen=True)
class TimeInterval:
    """Half-open time interval [start, end)."""
    start: datetime
    end: datetime

    def __post_init__(self):
        object.__setattr__(self, "start", ensure_utc(self.start))
        object.__setattr__(self, "end", ensure_utc(self.end))
        if self.start > self.end:
            raise ValueError(f"Interval start ({self.start}) cannot be strictly after end ({self.end})")

    @property
    def duration_minutes(self) -> float:
        """Duration of interval in minutes."""
        return (self.end - self.start).total_seconds() / 60.0

    def overlaps_with(self, other: "TimeInterval") -> bool:
        """Check if two half-open intervals overlap.
        
        Strict overlap condition for [start_A, end_A) and [start_B, end_B):
        max(start_A, start_B) < min(end_A, end_B)
        """
        return max(self.start, other.start) < min(self.end, other.end)

    def expand(self, buffer_before_minutes: int, buffer_after_minutes: int) -> "TimeInterval":
        """Expand interval with pre- and post-operational buffers."""
        new_start = self.start - timedelta(minutes=buffer_before_minutes)
        new_end = self.end + timedelta(minutes=buffer_after_minutes)
        return TimeInterval(start=new_start, end=new_end)


def calculate_slot_index(dt: datetime, slot_minutes: int = 5) -> int:
    """Map a datetime to its discrete daily time-slot index [0, 287].
    
    Formula per Zoutendijk & Mitici (2021):
    slot_index = floor(minutes_since_midnight / slot_minutes)
    """
    minutes_since_midnight = dt.hour * 60 + dt.minute + dt.second / 60.0
    slot = math.floor(minutes_since_midnight / slot_minutes)
    return min(max(slot, 0), int(1440 / slot_minutes) - 1)


def get_interval_slots(interval: TimeInterval, slot_minutes: int = 5) -> List[int]:
    """Return all discrete 5-minute slot indices covered by the interval within the same operational day."""
    start_slot = calculate_slot_index(interval.start, slot_minutes)
    end_slot = calculate_slot_index(interval.end, slot_minutes)

    if interval.end.date() > interval.start.date():
        # Crosses midnight: slots from start to 287, and 0 to end_slot
        total_daily_slots = int(1440 / slot_minutes)
        first_day_slots = list(range(start_slot, total_daily_slots))
        second_day_slots = list(range(0, end_slot + 1))
        return first_day_slots + second_day_slots

    return list(range(start_slot, max(start_slot, end_slot) + 1))


def build_gate_occupancy_interval(
    arrival_time: datetime,
    departure_time: Optional[datetime] = None,
    default_ground_time_minutes: int = 45,
    buffer_before_minutes: int = 0,
    buffer_after_minutes: int = 0,
) -> TimeInterval:
    """Build a half-open occupancy interval [start, end) for an aircraft gate visit.
    
    If departure time is not specified, uses arrival + default_ground_time_minutes.
    """
    start = arrival_time
    if departure_time is not None and departure_time > arrival_time:
        end = departure_time
    else:
        end = arrival_time + timedelta(minutes=default_ground_time_minutes)

    interval = TimeInterval(start=start, end=end)
    if buffer_before_minutes > 0 or buffer_after_minutes > 0:
        interval = interval.expand(buffer_before_minutes, buffer_after_minutes)

    return interval
