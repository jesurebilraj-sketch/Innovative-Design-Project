"""Unit tests for pure domain turnaround pairing logic."""

from datetime import datetime, timedelta, timezone
from app.domain.turnarounds import FlightLeg, pair_turnaround_leg


def test_turnaround_pairing_success():
    """Verify normal turnaround pairing selects earliest subsequent departure."""
    t0 = datetime(2026, 9, 22, 12, 0, tzinfo=timezone.utc)

    arr = FlightLeg(
        id="f-in",
        flight_number="KL101",
        aircraft_id="PH-BVA",
        origin_airport_id="AMS",
        destination_airport_id="RTM",
        scheduled_departure=t0 - timedelta(hours=1),
        scheduled_arrival=t0,
    )
    dep_later = FlightLeg(
        id="f-out-later",
        flight_number="KL104",
        aircraft_id="PH-BVA",
        origin_airport_id="RTM",
        destination_airport_id="JFK",
        scheduled_departure=t0 + timedelta(hours=3),
        scheduled_arrival=t0 + timedelta(hours=11),
    )
    dep_earlier = FlightLeg(
        id="f-out-early",
        flight_number="KL102",
        aircraft_id="PH-BVA",
        origin_airport_id="RTM",
        destination_airport_id="LHR",
        scheduled_departure=t0 + timedelta(minutes=60),
        scheduled_arrival=t0 + timedelta(minutes=120),
    )

    result = pair_turnaround_leg(arr, [dep_later, dep_earlier], minimum_turnaround_minutes=45)
    assert result.status == "MATCHED"
    assert result.departing_flight_id == "f-out-early"
    assert result.turnaround_buffer_minutes == 60.0
    assert result.is_feasible is True


def test_turnaround_unfeasible_buffer():
    """Verify pairing identifies insufficient turnaround buffer (< minimum)."""
    t0 = datetime(2026, 9, 22, 12, 0, tzinfo=timezone.utc)

    arr = FlightLeg(
        id="f-in",
        flight_number="KL101",
        aircraft_id="PH-BVA",
        origin_airport_id="AMS",
        destination_airport_id="RTM",
        scheduled_departure=t0 - timedelta(hours=1),
        scheduled_arrival=t0,
    )
    dep_tight = FlightLeg(
        id="f-out-tight",
        flight_number="KL102",
        aircraft_id="PH-BVA",
        origin_airport_id="RTM",
        destination_airport_id="LHR",
        scheduled_departure=t0 + timedelta(minutes=25),  # 25 min turnaround
        scheduled_arrival=t0 + timedelta(minutes=85),
    )

    result = pair_turnaround_leg(arr, [dep_tight], minimum_turnaround_minutes=45)
    assert result.status == "MATCHED"
    assert result.is_feasible is False
    assert result.turnaround_buffer_minutes == 25.0


def test_turnaround_missing_aircraft():
    """Verify missing aircraft ID returns INVALID_AIRCRAFT status."""
    t0 = datetime(2026, 9, 22, 12, 0, tzinfo=timezone.utc)

    arr = FlightLeg(
        id="f-in",
        flight_number="KL101",
        aircraft_id=None,
        origin_airport_id="AMS",
        destination_airport_id="RTM",
        scheduled_departure=t0 - timedelta(hours=1),
        scheduled_arrival=t0,
    )

    result = pair_turnaround_leg(arr, [], minimum_turnaround_minutes=45)
    assert result.status == "INVALID_AIRCRAFT"
    assert result.departing_flight_id is None


def test_turnaround_no_subsequent_leg():
    """Verify when no future leg exists returns NO_SUBSEQUENT_LEG."""
    t0 = datetime(2026, 9, 22, 12, 0, tzinfo=timezone.utc)

    arr = FlightLeg(
        id="f-in",
        flight_number="KL101",
        aircraft_id="PH-BVA",
        origin_airport_id="AMS",
        destination_airport_id="RTM",
        scheduled_departure=t0 - timedelta(hours=1),
        scheduled_arrival=t0,
    )

    result = pair_turnaround_leg(arr, [], minimum_turnaround_minutes=45)
    assert result.status == "NO_SUBSEQUENT_LEG"
    assert result.departing_flight_id is None
