"""Weather service coordinating airport weather queries and persistence."""

from datetime import datetime, timezone
from typing import Optional
from sqlalchemy.orm import Session
from app.core.exceptions import AirportNotFoundError, WeatherProviderError
from app.db.models import Weather
from app.integrations.weather import OpenMeteoClient
from app.repositories.airports import AirportRepository
from app.repositories.weather import WeatherRepository
from app.schemas.weather import WeatherResponse, WeatherSnapshot


class WeatherService:
    """Service handling weather queries, external retrieval, and caching."""

    def __init__(self, db: Session, weather_client: Optional[OpenMeteoClient] = None):
        self.db = db
        self.airport_repo = AirportRepository(db)
        self.weather_repo = WeatherRepository(db)
        self.client = weather_client or OpenMeteoClient()

    def get_weather_for_airport(
        self, airport_id: str, target_time: Optional[datetime] = None
    ) -> WeatherResponse:
        """Retrieve current or specified weather for an airport, fetching from Open-Meteo if needed."""
        airport = self.airport_repo.get_by_id(airport_id)
        if not airport:
            raise AirportNotFoundError(airport_id)

        target = target_time or datetime.now(timezone.utc)

        # Check repository for existing recent observation
        existing = self.weather_repo.get_weather_for_timestamp(airport_id, target)
        if existing:
            return WeatherResponse.model_validate(existing)

        # Fetch from Open-Meteo integration
        snapshot = self.client.get_weather(airport.latitude, airport.longitude, target)
        if not snapshot:
            # Fall back to latest known or return empty baseline
            latest = self.weather_repo.get_latest_for_airport(airport_id)
            if latest:
                return WeatherResponse.model_validate(latest)
            # Create a neutral baseline observation if completely offline
            snapshot = WeatherSnapshot(
                observed_at=target,
                temperature_c=15.0,
                precipitation_mm=0.0,
                visibility_km=10.0,
                wind_speed_mps=3.0,
                cloud_cover_pct=20.0,
                source="fallback-baseline",
            )

        # Persist observation to database
        weather_record = Weather(
            airport_id=airport_id,
            observed_at=snapshot.observed_at,
            temperature_c=snapshot.temperature_c,
            precipitation_mm=snapshot.precipitation_mm,
            rain_mm=snapshot.rain_mm,
            visibility_km=snapshot.visibility_km,
            wind_speed_mps=snapshot.wind_speed_mps,
            wind_direction_deg=snapshot.wind_direction_deg,
            pressure_hpa=snapshot.pressure_hpa,
            cloud_cover_pct=snapshot.cloud_cover_pct,
            source=snapshot.source,
        )
        saved = self.weather_repo.create(weather_record)
        return WeatherResponse.model_validate(saved)
