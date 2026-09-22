"""Gate repository for database operations."""

from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from app.db.models import Gate, GateAssignment
from app.repositories.base import BaseRepository


class GateRepository(BaseRepository[Gate]):
    """Repository handling Gate and GateAssignment database operations."""

    def __init__(self, db: Session):
        super().__init__(Gate, db)

    def list_by_airport(self, airport_id: str, active_only: bool = True) -> List[Gate]:
        """Retrieve all gates for a given airport, optionally filtered by active status."""
        query = self.db.query(Gate).filter(Gate.airport_id == airport_id)
        if active_only:
            query = query.filter(Gate.is_active.is_(True))
        return query.order_by(Gate.terminal, Gate.gate_code).all()

    def get_by_code(self, airport_id: str, gate_code: str) -> Optional[Gate]:
        """Retrieve a specific gate by airport ID and gate code."""
        return (
            self.db.query(Gate)
            .filter(Gate.airport_id == airport_id, Gate.gate_code == gate_code)
            .first()
        )

    def get_assignments_in_window(
        self, airport_id: str, start_time: datetime, end_time: datetime
    ) -> List[GateAssignment]:
        """Retrieve all gate assignments overlapping with the specified time interval [start_time, end_time].
        
        Overlap condition: max(valid_from, start_time) < min(valid_to, end_time),
        which translates to: valid_from < end_time AND valid_to > start_time.
        """
        return (
            self.db.query(GateAssignment)
            .join(Gate, GateAssignment.gate_id == Gate.id)
            .filter(
                Gate.airport_id == airport_id,
                GateAssignment.valid_from < end_time,
                GateAssignment.valid_to > start_time,
            )
            .all()
        )

    def create_assignment(self, assignment: GateAssignment) -> GateAssignment:
        """Persist a new gate assignment."""
        self.db.add(assignment)
        self.db.commit()
        self.db.refresh(assignment)
        return assignment
