"""Weather API endpoints."""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.weather import WeatherResponse
from app.services.weather import WeatherService

router = APIRouter()


@router.get("/airport/{airport_id}", response_model=WeatherResponse, summary="Get airport weather")
def get_airport_weather(
    airport_id: str,
    target_time: Optional[datetime] = Query(None, description="Optional target UTC timestamp (defaults to current time)"),
    db: Session = Depends(get_db),
):
    """Retrieve normalized surface weather metrics for an aerodrome.
    
    Coordinates with database cache and live Open-Meteo integration.
    """
    service = WeatherService(db)
    return service.get_weather_for_airport(airport_id, target_time=target_time)
