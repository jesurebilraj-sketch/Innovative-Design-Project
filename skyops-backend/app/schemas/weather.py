"""Pydantic schemas for weather observations and Open-Meteo responses."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class WeatherBase(BaseModel):
    airport_id: str
    observed_at: datetime
    temperature_c: Optional[float] = Field(None, description="Temperature in Celsius")
    precipitation_mm: Optional[float] = Field(None, description="Precipitation in mm")
    rain_mm: Optional[float] = Field(None, description="Rainfall in mm")
    visibility_km: Optional[float] = Field(None, description="Visibility in km")
    wind_speed_mps: Optional[float] = Field(None, description="Wind speed in meters per second")
    wind_direction_deg: Optional[float] = Field(None, ge=0, le=360, description="Wind direction in degrees")
    pressure_hpa: Optional[float] = Field(None, description="Atmospheric pressure in hPa")
    cloud_cover_pct: Optional[float] = Field(None, ge=0, le=100, description="Cloud cover percentage")
    source: str = "open-meteo"


class WeatherResponse(WeatherBase):
    id: str
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class WeatherSnapshot(BaseModel):
    """Normalized snapshot payload from weather integration."""
    observed_at: datetime
    temperature_c: Optional[float] = None
    precipitation_mm: Optional[float] = None
    rain_mm: Optional[float] = None
    visibility_km: Optional[float] = None
    wind_speed_mps: Optional[float] = None
    wind_direction_deg: Optional[float] = None
    pressure_hpa: Optional[float] = None
    cloud_cover_pct: Optional[float] = None
    source: str = "open-meteo"
