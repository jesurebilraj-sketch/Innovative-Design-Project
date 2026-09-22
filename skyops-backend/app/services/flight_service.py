"""Flight service coordinating flight queries and operational turnaround detection."""

from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from app.core.exceptions import FlightNotFoundError
from app.core.settings import settings
from app.domain.turnarounds import FlightLeg, pair_turnaround_leg
from app.repositories.flights import FlightRepository
from app.schemas.flight import FlightDetailResponse, FlightResponse, TurnaroundLegResponse


class FlightService:
    """Service handling flight operations and turnaround pairing."""

    def __init__(self, db: Session):
        self.db = db
        self.flight_repo = FlightRepository(db)

    def list_flights(
        self,
        airport_id: Optional[str] = None,
        airline_code: Optional[str] = None,
        status: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> List[FlightResponse]:
        """List flights with optional filtering."""
        flights = self.flight_repo.list_flights(
            airport_id=airport_id,
            airline_code=airline_code,
            status=status,
            start_time=start_time,
            end_time=end_time,
            skip=skip,
            limit=limit,
        )
        return [FlightResponse.model_validate(f) for f in flights]

    def get_flight(self, flight_id: str) -> FlightDetailResponse:
        """Retrieve a single flight with origin and destination aerodromes."""
        flight = self.flight_repo.get_by_id(flight_id)
        if not flight:
            raise FlightNotFoundError(flight_id)
        return FlightDetailResponse.model_validate(flight)

    def get_turnaround_leg(
        self, flight_id: str, minimum_turnaround_minutes: Optional[int] = None
    ) -> TurnaroundLegResponse:
        """Identify the next outbound departure for the arriving aircraft at the destination airport.
        
        Applies pure domain turnaround logic per GEMINI_BACKEND.md Section 16.
        """
        flight = self.flight_repo.get_by_id(flight_id)
        if not flight:
            raise FlightNotFoundError(flight_id)

        min_buffer = minimum_turnaround_minutes or settings.MIN_TURNAROUND_MINUTES

        arriving_leg = FlightLeg(
            id=flight.id,
            flight_number=flight.flight_number,
            aircraft_id=flight.aircraft_id,
            origin_airport_id=flight.origin_airport_id,
            destination_airport_id=flight.destination_airport_id,
            scheduled_departure=flight.scheduled_departure,
            scheduled_arrival=flight.scheduled_arrival,
            actual_departure=flight.actual_departure,
            actual_arrival=flight.actual_arrival,
            cancelled=flight.cancelled,
        )

        candidate_departures: List[FlightLeg] = []
        if flight.aircraft_id:
            # Query candidate flights operated by the same aircraft from this destination airport
            db_candidates = self.flight_repo.find_subsequent_flights_for_aircraft(
                aircraft_id=flight.aircraft_id,
                origin_airport_id=flight.destination_airport_id,
                after_time=flight.actual_arrival or flight.scheduled_arrival,
            )
            for cand in db_candidates:
                candidate_departures.append(
                    FlightLeg(
                        id=cand.id,
                        flight_number=cand.flight_number,
                        aircraft_id=cand.aircraft_id,
                        origin_airport_id=cand.origin_airport_id,
                        destination_airport_id=cand.destination_airport_id,
                        scheduled_departure=cand.scheduled_departure,
                        scheduled_arrival=cand.scheduled_arrival,
                        actual_departure=cand.actual_departure,
                        actual_arrival=cand.actual_arrival,
                        cancelled=cand.cancelled,
                    )
                )

        pairing = pair_turnaround_leg(
            arriving_leg=arriving_leg,
            candidate_departures=candidate_departures,
            minimum_turnaround_minutes=min_buffer,
        )

        return TurnaroundLegResponse(
            arriving_flight_id=pairing.arriving_flight_id,
            arriving_flight_number=pairing.arriving_flight_number,
            departing_flight_id=pairing.departing_flight_id,
            departing_flight_number=pairing.departing_flight_number,
            aircraft_id=pairing.aircraft_id,
            airport_id=pairing.airport_id,
            arrival_time=pairing.arrival_time,
            scheduled_departure_time=pairing.scheduled_departure_time,
            turnaround_buffer_minutes=pairing.turnaround_buffer_minutes,
            minimum_required_minutes=pairing.minimum_required_minutes,
            is_feasible=pairing.is_feasible,
            status=pairing.status,
        )
