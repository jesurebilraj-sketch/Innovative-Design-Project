"""Airport repository for database operations."""

from typing import Optional, List
from sqlalchemy.orm import Session
from app.db.models import Airport
from app.repositories.base import BaseRepository


class AirportRepository(BaseRepository[Airport]):
    """Repository handling Airport entity queries."""

    def __init__(self, db: Session):
        super().__init__(Airport, db)

    def get_by_iata(self, iata_code: str) -> Optional[Airport]:
        """Lookup airport by 3-letter IATA code."""
        return self.db.query(Airport).filter(Airport.iata_code == iata_code.upper()).first()

    def get_by_icao(self, icao_code: str) -> Optional[Airport]:
        """Lookup airport by 4-letter ICAO code."""
        return self.db.query(Airport).filter(Airport.icao_code == icao_code.upper()).first()

    def list_all(self, skip: int = 0, limit: int = 100) -> List[Airport]:
        """List airports ordered by IATA code."""
        return self.db.query(Airport).order_by(Airport.iata_code).offset(skip).limit(limit).all()
