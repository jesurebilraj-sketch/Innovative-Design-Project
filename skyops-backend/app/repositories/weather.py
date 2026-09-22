"""Weather repository for database operations."""

from datetime import datetime
from typing import List, Optional
from sqlalchemy.orm import Session
from app.db.models import Weather
from app.repositories.base import BaseRepository


class WeatherRepository(BaseRepository[Weather]):
    """Repository handling Weather entity queries and persistence."""

    def __init__(self, db: Session):
        super().__init__(Weather, db)

    def get_latest_for_airport(self, airport_id: str) -> Optional[Weather]:
        """Retrieve most recent weather observation for an airport."""
        return (
            self.db.query(Weather)
            .filter(Weather.airport_id == airport_id)
            .order_by(Weather.observed_at.desc())
            .first()
        )

    def get_weather_for_timestamp(
        self, airport_id: str, target_time: datetime
    ) -> Optional[Weather]:
        """Retrieve weather observation closest to a specific timestamp within +/- 2 hours."""
        # Query nearest observation
        records = (
            self.db.query(Weather)
            .filter(Weather.airport_id == airport_id)
            .order_by(Weather.observed_at.desc())
            .limit(10)
            .all()
        )
        if not records:
            return None

        # Pick record with minimum time difference
        best_record = min(
            records,
            key=lambda w: abs((w.observed_at - target_time).total_seconds()),
        )
        # If difference <= 3 hours (10800s), accept it
        if abs((best_record.observed_at - target_time).total_seconds()) <= 10800:
            return best_record
        return None
