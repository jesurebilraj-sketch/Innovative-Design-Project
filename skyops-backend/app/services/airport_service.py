"""Airport service coordinating aerodrome queries."""

from typing import List, Optional
from sqlalchemy.orm import Session
from app.core.exceptions import AirportNotFoundError
from app.repositories.airports import AirportRepository
from app.repositories.gates import GateRepository
from app.schemas.airport import AirportCreate, AirportResponse
from app.schemas.gate import GateResponse
from app.db.models import Airport


class AirportService:
    """Service handling airport and associated gate retrieval."""

    def __init__(self, db: Session):
        self.db = db
        self.airport_repo = AirportRepository(db)
        self.gate_repo = GateRepository(db)

    def list_airports(self, skip: int = 0, limit: int = 100) -> List[AirportResponse]:
        """List all airports."""
        airports = self.airport_repo.list_all(skip=skip, limit=limit)
        return [AirportResponse.model_validate(a) for a in airports]

    def get_airport(self, airport_id: str) -> AirportResponse:
        """Retrieve a specific airport by ID or 3-letter IATA code."""
        airport = self.airport_repo.get_by_id(airport_id)
        if not airport and len(airport_id) == 3:
            airport = self.airport_repo.get_by_iata(airport_id)

        if not airport:
            raise AirportNotFoundError(airport_id)
        return AirportResponse.model_validate(airport)

    def list_airport_gates(self, airport_id: str) -> List[GateResponse]:
        """Retrieve all active gates for an airport."""
        airport = self.get_airport(airport_id)
        gates = self.gate_repo.list_by_airport(airport.id)
        return [GateResponse.model_validate(g) for g in gates]

    def create_airport(self, data: AirportCreate) -> AirportResponse:
        """Register a new airport."""
        airport = Airport(
            iata_code=data.iata_code.upper(),
            icao_code=data.icao_code.upper() if data.icao_code else None,
            name=data.name,
            city=data.city,
            country=data.country,
            latitude=data.latitude,
            longitude=data.longitude,
            timezone=data.timezone,
        )
        saved = self.airport_repo.create(airport)
        return AirportResponse.model_validate(saved)
