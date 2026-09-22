"""Domain logic for gate availability and conflict checking.

Research Basis:
- Zoutendijk & Mitici (2021) & Zhang & Klabjan (2017):
  Deterministic Flight-to-Gate Assignment Problem (FGAP) requires that at any time slot t,
  a gate j may be occupied by at most one aircraft: sum_i s_it * x_ijt <= 1.
- Half-open intervals [start, end) prevent false positive boundary conflicts.
- Aircraft size compatibility ensures physical capability constraints are satisfied.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple
from app.domain.presence import TimeInterval


# Aircraft size hierarchy: higher rank requires larger gate
AIRCRAFT_SIZE_RANK = {
    "REGIONAL": 1,
    "NARROW_BODY": 2,
    "WIDE_BODY": 3,
}


@dataclass(frozen=True)
class GateDomain:
    """Pure domain gate representation."""
    id: str
    gate_code: str
    terminal: str
    airport_id: str
    aircraft_size_limit: str  # REGIONAL, NARROW_BODY, WIDE_BODY
    is_active: bool = True


@dataclass(frozen=True)
class ExistingAssignment:
    """Existing gate assignment with its half-open occupancy interval."""
    id: str
    flight_id: str
    gate_id: str
    interval: TimeInterval


@dataclass(frozen=True)
class ConflictCheckResult:
    """Result of gate availability and operational conflict evaluation."""
    is_available: bool
    is_compatible: bool
    has_conflict: bool
    reason: str
    conflicting_flight_ids: List[str]


def is_aircraft_compatible_with_gate(aircraft_size: str, gate_size_limit: str) -> bool:
    """Verify if the aircraft size fits within the gate size limit.
    
    A gate can host an aircraft if gate_rank >= aircraft_rank.
    e.g. A WIDE_BODY gate can host REGIONAL, NARROW_BODY, and WIDE_BODY.
    """
    req_rank = AIRCRAFT_SIZE_RANK.get(aircraft_size.upper(), 2)  # default NARROW_BODY
    gate_rank = AIRCRAFT_SIZE_RANK.get(gate_size_limit.upper(), 2)
    return gate_rank >= req_rank


def check_gate_availability(
    gate: GateDomain,
    requested_interval: TimeInterval,
    aircraft_size: str,
    existing_assignments: List[ExistingAssignment],
    requesting_flight_id: Optional[str] = None,
) -> ConflictCheckResult:
    """Evaluate whether a gate is available for a requested interval without conflicts.
    
    Checks:
    1. Gate active status.
    2. Aircraft size compatibility.
    3. Overlap with existing assignments at this gate (excluding the same flight if re-checking).
    """
    if not gate.is_active:
        return ConflictCheckResult(
            is_available=False,
            is_compatible=False,
            has_conflict=False,
            reason=f"Gate {gate.gate_code} is currently inactive or closed",
            conflicting_flight_ids=[],
        )

    if not is_aircraft_compatible_with_gate(aircraft_size, gate.aircraft_size_limit):
        return ConflictCheckResult(
            is_available=False,
            is_compatible=False,
            has_conflict=False,
            reason=f"Aircraft size '{aircraft_size}' exceeds gate limit '{gate.aircraft_size_limit}'",
            conflicting_flight_ids=[],
        )

    # Check for overlapping occupancy intervals at this gate
    conflicting_ids = []
    for assignment in existing_assignments:
        if assignment.gate_id != gate.id:
            continue
        # Skip if it is the flight's own existing assignment being modified/reassessed
        if requesting_flight_id and assignment.flight_id == requesting_flight_id:
            continue

        if requested_interval.overlaps_with(assignment.interval):
            conflicting_ids.append(assignment.flight_id)

    if conflicting_ids:
        return ConflictCheckResult(
            is_available=False,
            is_compatible=True,
            has_conflict=True,
            reason=f"Conflict detected with {len(conflicting_ids)} active assignment(s) at Gate {gate.gate_code}",
            conflicting_flight_ids=conflicting_ids,
        )

    return ConflictCheckResult(
        is_available=True,
        is_compatible=True,
        has_conflict=False,
        reason=f"Gate {gate.gate_code} is available and compatible",
        conflicting_flight_ids=[],
    )
