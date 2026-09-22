"""Unit tests for gate conflict detection and aircraft size compatibility."""

from datetime import datetime, timedelta, timezone
from app.domain.gate_assignment import (
    ExistingAssignment,
    GateDomain,
    check_gate_availability,
    is_aircraft_compatible_with_gate,
)
from app.domain.presence import TimeInterval


def test_aircraft_size_compatibility():
    """Verify aircraft size compatibility rules."""
    # Regional aircraft can use any gate
    assert is_aircraft_compatible_with_gate("REGIONAL", "REGIONAL") is True
    assert is_aircraft_compatible_with_gate("REGIONAL", "NARROW_BODY") is True
    assert is_aircraft_compatible_with_gate("REGIONAL", "WIDE_BODY") is True

    # Narrow-body cannot use regional gate
    assert is_aircraft_compatible_with_gate("NARROW_BODY", "REGIONAL") is False
    assert is_aircraft_compatible_with_gate("NARROW_BODY", "NARROW_BODY") is True
    assert is_aircraft_compatible_with_gate("NARROW_BODY", "WIDE_BODY") is True

    # Wide-body can only use wide-body gate
    assert is_aircraft_compatible_with_gate("WIDE_BODY", "REGIONAL") is False
    assert is_aircraft_compatible_with_gate("WIDE_BODY", "NARROW_BODY") is False
    assert is_aircraft_compatible_with_gate("WIDE_BODY", "WIDE_BODY") is True


def test_gate_conflict_detected():
    """Verify conflict detected when requested interval overlaps existing assignment."""
    t0 = datetime(2026, 9, 22, 10, 0, tzinfo=timezone.utc)
    gate = GateDomain(
        id="g-01",
        gate_code="G01",
        terminal="T1",
        airport_id="RTM",
        aircraft_size_limit="NARROW_BODY",
        is_active=True,
    )

    # Existing assignment: 10:00 - 11:00
    existing = [
        ExistingAssignment(
            id="asg-1",
            flight_id="flight-101",
            gate_id="g-01",
            interval=TimeInterval(start=t0, end=t0 + timedelta(hours=1)),
        )
    ]

    # Requested interval: 10:30 - 11:30 (overlaps)
    req_interval = TimeInterval(start=t0 + timedelta(minutes=30), end=t0 + timedelta(minutes=90))
    result = check_gate_availability(
        gate=gate,
        requested_interval=req_interval,
        aircraft_size="NARROW_BODY",
        existing_assignments=existing,
    )

    assert result.is_available is False
    assert result.has_conflict is True
    assert "flight-101" in result.conflicting_flight_ids


def test_gate_no_conflict_when_adjacent():
    """Verify no conflict when intervals touch at boundary [10:00, 11:00) and [11:00, 12:00)."""
    t0 = datetime(2026, 9, 22, 10, 0, tzinfo=timezone.utc)
    gate = GateDomain(
        id="g-01",
        gate_code="G01",
        terminal="T1",
        airport_id="RTM",
        aircraft_size_limit="NARROW_BODY",
        is_active=True,
    )

    existing = [
        ExistingAssignment(
            id="asg-1",
            flight_id="flight-101",
            gate_id="g-01",
            interval=TimeInterval(start=t0, end=t0 + timedelta(hours=1)),
        )
    ]

    # Requested interval starts exactly at 11:00
    req_interval = TimeInterval(start=t0 + timedelta(hours=1), end=t0 + timedelta(hours=2))
    result = check_gate_availability(
        gate=gate,
        requested_interval=req_interval,
        aircraft_size="NARROW_BODY",
        existing_assignments=existing,
    )

    assert result.is_available is True
    assert result.has_conflict is False
    assert len(result.conflicting_flight_ids) == 0


def test_inactive_gate_rejected():
    """Verify inactive gate is rejected even if interval is free."""
    t0 = datetime(2026, 9, 22, 10, 0, tzinfo=timezone.utc)
    gate = GateDomain(
        id="g-01",
        gate_code="G01",
        terminal="T1",
        airport_id="RTM",
        aircraft_size_limit="NARROW_BODY",
        is_active=False,
    )

    req_interval = TimeInterval(start=t0, end=t0 + timedelta(hours=1))
    result = check_gate_availability(
        gate=gate,
        requested_interval=req_interval,
        aircraft_size="NARROW_BODY",
        existing_assignments=[],
    )

    assert result.is_available is False
    assert "inactive" in result.reason
