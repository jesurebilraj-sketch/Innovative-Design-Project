"""Flight repository for database operations."""

from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.db.models import Flight
from app.repositories.base import BaseRepository


class FlightRepository(BaseRepository[Flight]):
    """Repository handling Flight entity queries and rotation lookups."""

    def __init__(self, db: Session):
        super().__init__(Flight, db)

    def list_flights(
        self,
        airport_id: Optional[str] = None,
        airline_code: Optional[str] = None,
        status: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[Flight]:
        """List flights with optional filters for airport, airline, status, and time range."""
        query = self.db.query(Flight)

        if airport_id:
            query = query.filter(
                or_(
                    Flight.origin_airport_id == airport_id,
                    Flight.destination_airport_id == airport_id,
                )
            )
        if airline_code:
            query = query.filter(Flight.airline_code == airline_code.upper())
        if status:
            query = query.filter(Flight.status == status.upper())
        if start_time:
            query = query.filter(Flight.scheduled_departure >= start_time)
        if end_time:
            query = query.filter(Flight.scheduled_departure <= end_time)

        return (
            query.order_by(Flight.scheduled_departure.asc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def find_subsequent_flights_for_aircraft(
        self, aircraft_id: str, origin_airport_id: str, after_time: datetime
    ) -> List[Flight]:
        """Retrieve future flights operated by the same aircraft from the given airport.
        
        Ordered chronologically to facilitate turnaround pairing.
        """
        return (
            self.db.query(Flight)
            .filter(
                Flight.aircraft_id == aircraft_id,
                Flight.origin_airport_id == origin_airport_id,
                Flight.scheduled_departure > after_time,
                Flight.cancelled.is_(False),
            )
            .order_by(Flight.scheduled_departure.asc())
            .all()
        )

    def get_flight_rotation(self, aircraft_id: str, start_time: datetime) -> List[Flight]:
        """Retrieve chronological sequence of flights for an aircraft from start_time."""
        return (
            self.db.query(Flight)
            .filter(
                Flight.aircraft_id == aircraft_id,
                Flight.scheduled_departure >= start_time,
                Flight.cancelled.is_(False),
            )
            .order_by(Flight.scheduled_departure.asc())
            .all()
        )
