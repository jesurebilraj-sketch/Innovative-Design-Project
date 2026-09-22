"""Gate service coordinating gate availability, conflict checking, and allocations."""

from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from app.core.exceptions import GateNotFoundError
from app.domain.gate_assignment import (
    ExistingAssignment,
    GateDomain,
    check_gate_availability,
)
from app.domain.presence import TimeInterval
from app.repositories.gates import GateRepository
from app.schemas.gate import GateAvailabilityCheckRequest, GateAvailabilityResponse


class GateService:
    """Service handling gate availability queries and conflict validation."""

    def __init__(self, db: Session):
        self.db = db
        self.gate_repo = GateRepository(db)

    def check_availability(
        self, request: GateAvailabilityCheckRequest
    ) -> GateAvailabilityResponse:
        """Verify whether a gate is available without conflicts during a requested interval."""
        gate = self.gate_repo.get_by_id(request.gate_id)
        if not gate:
            raise GateNotFoundError(request.gate_id)

        domain_gate = GateDomain(
            id=gate.id,
            gate_code=gate.gate_code,
            terminal=gate.terminal,
            airport_id=gate.airport_id,
            aircraft_size_limit=gate.aircraft_size_limit,
            is_active=gate.is_active,
        )

        requested_interval = TimeInterval(
            start=request.start_time,
            end=request.end_time,
        )

        # Retrieve active assignments for this airport in the requested time window
        db_assignments = self.gate_repo.get_assignments_in_window(
            airport_id=gate.airport_id,
            start_time=request.start_time,
            end_time=request.end_time,
        )

        existing_assignments = [
            ExistingAssignment(
                id=a.id,
                flight_id=a.flight_id,
                gate_id=a.gate_id,
                interval=TimeInterval(start=a.valid_from, end=a.valid_to),
            )
            for a in db_assignments
        ]

        result = check_gate_availability(
            gate=domain_gate,
            requested_interval=requested_interval,
            aircraft_size=request.aircraft_size or "NARROW_BODY",
            existing_assignments=existing_assignments,
        )

        return GateAvailabilityResponse(
            gate_id=gate.id,
            is_available=result.is_available,
            is_compatible=result.is_compatible,
            has_conflict=result.has_conflict,
            reason=result.reason,
            conflicting_flight_ids=result.conflicting_flight_ids,
        )
