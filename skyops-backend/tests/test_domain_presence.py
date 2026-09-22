"""Unit tests for gate presence, half-open intervals, and 5-minute time slots."""

from datetime import datetime, timezone
import pytest
from app.domain.presence import (
    TimeInterval,
    build_gate_occupancy_interval,
    calculate_slot_index,
    get_interval_slots,
)


def test_half_open_interval_boundary_no_conflict():
    """Verify adjacent half-open intervals [10:00, 10:30) and [10:30, 11:00) do NOT overlap."""
    t1 = datetime(2026, 9, 22, 10, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 9, 22, 10, 30, tzinfo=timezone.utc)
    t3 = datetime(2026, 9, 22, 11, 0, tzinfo=timezone.utc)

    inv1 = TimeInterval(start=t1, end=t2)
    inv2 = TimeInterval(start=t2, end=t3)

    assert inv1.overlaps_with(inv2) is False
    assert inv2.overlaps_with(inv1) is False


def test_overlapping_intervals():
    """Verify overlapping intervals [10:00, 10:35) and [10:30, 11:00) detect overlap."""
    t1 = datetime(2026, 9, 22, 10, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 9, 22, 10, 35, tzinfo=timezone.utc)
    t3 = datetime(2026, 9, 22, 10, 30, tzinfo=timezone.utc)
    t4 = datetime(2026, 9, 22, 11, 0, tzinfo=timezone.utc)

    inv1 = TimeInterval(start=t1, end=t2)
    inv2 = TimeInterval(start=t3, end=t4)

    assert inv1.overlaps_with(inv2) is True
    assert inv2.overlaps_with(inv1) is True


def test_interval_invalid_start_after_end():
    """Verify TimeInterval rejects start > end."""
    t1 = datetime(2026, 9, 22, 11, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 9, 22, 10, 0, tzinfo=timezone.utc)

    with pytest.raises(ValueError):
        TimeInterval(start=t1, end=t2)


def test_calculate_5min_slot_index():
    """Verify 5-minute time slot index calculations (288 slots/day)."""
    # 00:00 -> slot 0
    dt0 = datetime(2026, 9, 22, 0, 0, tzinfo=timezone.utc)
    assert calculate_slot_index(dt0) == 0

    # 00:04 -> slot 0
    dt1 = datetime(2026, 9, 22, 0, 4, tzinfo=timezone.utc)
    assert calculate_slot_index(dt1) == 0

    # 00:05 -> slot 1
    dt2 = datetime(2026, 9, 22, 0, 5, tzinfo=timezone.utc)
    assert calculate_slot_index(dt2) == 1

    # 23:55 -> slot 287
    dt3 = datetime(2026, 9, 22, 23, 55, tzinfo=timezone.utc)
    assert calculate_slot_index(dt3) == 287


def test_interval_buffer_expansion():
    """Verify buffer expansion extends start and end correctly."""
    t1 = datetime(2026, 9, 22, 10, 0, tzinfo=timezone.utc)
    t2 = datetime(2026, 9, 22, 11, 0, tzinfo=timezone.utc)

    interval = TimeInterval(start=t1, end=t2)
    expanded = interval.expand(buffer_before_minutes=15, buffer_after_minutes=10)

    assert expanded.start == datetime(2026, 9, 22, 9, 45, tzinfo=timezone.utc)
    assert expanded.end == datetime(2026, 9, 22, 11, 10, tzinfo=timezone.utc)
    assert expanded.duration_minutes == 85.0
