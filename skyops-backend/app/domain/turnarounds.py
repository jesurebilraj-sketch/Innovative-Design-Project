"""Domain logic for aircraft turnaround pairing.

Research Basis:
- Sternberg et al. (2017) & Zhang et al. (2021): Delays propagate across sequential legs
  operated by the same physical aircraft (aircraft rotation).
- Turnaround pairing matches an arriving flight with the aircraft's next outbound flight
  at the same aerodrome.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional, Tuple


@dataclass(frozen=True)
class FlightLeg:
    """Lightweight pure domain object representing a flight leg."""
    id: str
    flight_number: str
    aircraft_id: Optional[str]
    origin_airport_id: str
    destination_airport_id: str
    scheduled_departure: datetime
    scheduled_arrival: datetime
    actual_departure: Optional[datetime] = None
    actual_arrival: Optional[datetime] = None
    cancelled: bool = False


@dataclass(frozen=True)
class TurnaroundPairing:
    """Result of turnaround pairing analysis."""
    arriving_flight_id: str
    arriving_flight_number: str
    departing_flight_id: Optional[str]
    departing_flight_number: Optional[str]
    aircraft_id: Optional[str]
    airport_id: str
    arrival_time: datetime
    scheduled_departure_time: Optional[datetime]
    turnaround_buffer_minutes: Optional[float]
    minimum_required_minutes: int
    is_feasible: bool
    status: str  # MATCHED, NO_SUBSEQUENT_LEG, INVALID_AIRCRAFT, CANCELLED


def ensure_utc(dt: Optional[datetime]) -> Optional[datetime]:
    """Ensure datetime is timezone-aware UTC per GEMINI_BACKEND.md Section 14."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def get_effective_arrival_time(leg: FlightLeg) -> Optional[datetime]:
    """Return actual arrival if known, otherwise scheduled arrival (normalized to UTC)."""
    val = leg.actual_arrival or leg.scheduled_arrival
    return ensure_utc(val)


def get_effective_departure_time(leg: FlightLeg) -> Optional[datetime]:
    """Return actual departure if known, otherwise scheduled departure (normalized to UTC)."""
    val = leg.actual_departure or leg.scheduled_departure
    return ensure_utc(val)


def pair_turnaround_leg(
    arriving_leg: FlightLeg,
    candidate_departures: List[FlightLeg],
    minimum_turnaround_minutes: int = 45,
) -> TurnaroundPairing:
    """Find the immediate next departure for the arriving aircraft at the destination airport.
    
    Validation rules:
    1. Aircraft identifier must be non-empty.
    2. Candidate legs must be operated by the same aircraft.
    3. Candidate legs must depart from the arriving leg's destination airport.
    4. Candidate leg departure must be strictly chronologically AFTER arrival time.
    5. Earliest chronological candidate is selected.
    """
    arrival_time = get_effective_arrival_time(arriving_leg)
    dest_airport = arriving_leg.destination_airport_id

    if not arriving_leg.aircraft_id:
        return TurnaroundPairing(
            arriving_flight_id=arriving_leg.id,
            arriving_flight_number=arriving_leg.flight_number,
            departing_flight_id=None,
            departing_flight_number=None,
            aircraft_id=None,
            airport_id=dest_airport,
            arrival_time=arrival_time,
            scheduled_departure_time=None,
            turnaround_buffer_minutes=None,
            minimum_required_minutes=minimum_turnaround_minutes,
            is_feasible=False,
            status="INVALID_AIRCRAFT",
        )

    if arriving_leg.cancelled:
        return TurnaroundPairing(
            arriving_flight_id=arriving_leg.id,
            arriving_flight_number=arriving_leg.flight_number,
            departing_flight_id=None,
            departing_flight_number=None,
            aircraft_id=arriving_leg.aircraft_id,
            airport_id=dest_airport,
            arrival_time=arrival_time,
            scheduled_departure_time=None,
            turnaround_buffer_minutes=None,
            minimum_required_minutes=minimum_turnaround_minutes,
            is_feasible=False,
            status="CANCELLED",
        )

    # Filter candidates
    valid_candidates = []
    for dep in candidate_departures:
        if dep.cancelled:
            continue
        if dep.aircraft_id != arriving_leg.aircraft_id:
            continue
        if dep.origin_airport_id != dest_airport:
            continue
        dep_time = get_effective_departure_time(dep)
        if dep_time is not None and dep_time > arrival_time:
            valid_candidates.append((dep_time, dep))

    if not valid_candidates:
        return TurnaroundPairing(
            arriving_flight_id=arriving_leg.id,
            arriving_flight_number=arriving_leg.flight_number,
            departing_flight_id=None,
            departing_flight_number=None,
            aircraft_id=arriving_leg.aircraft_id,
            airport_id=dest_airport,
            arrival_time=arrival_time,
            scheduled_departure_time=None,
            turnaround_buffer_minutes=None,
            minimum_required_minutes=minimum_turnaround_minutes,
            is_feasible=True,  # No immediate leg means aircraft rests or stays overnight
            status="NO_SUBSEQUENT_LEG",
        )

    # Pick earliest departure
    valid_candidates.sort(key=lambda pair: pair[0])
    next_departure_time, next_leg = valid_candidates[0]

    buffer_minutes = (next_departure_time - arrival_time).total_seconds() / 60.0
    is_feasible = buffer_minutes >= minimum_turnaround_minutes

    return TurnaroundPairing(
        arriving_flight_id=arriving_leg.id,
        arriving_flight_number=arriving_leg.flight_number,
        departing_flight_id=next_leg.id,
        departing_flight_number=next_leg.flight_number,
        aircraft_id=arriving_leg.aircraft_id,
        airport_id=dest_airport,
        arrival_time=arrival_time,
        scheduled_departure_time=next_departure_time,
        turnaround_buffer_minutes=round(buffer_minutes, 2),
        minimum_required_minutes=minimum_turnaround_minutes,
        is_feasible=is_feasible,
        status="MATCHED",
    )
