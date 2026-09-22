"""Pydantic schemas for airports."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


class AirportBase(BaseModel):
    iata_code: str = Field(..., min_length=3, max_length=3, description="3-letter IATA code")
    icao_code: Optional[str] = Field(None, min_length=4, max_length=4, description="4-letter ICAO code")
    name: str = Field(..., description="Airport full name")
    city: str = Field(..., description="City")
    country: str = Field(..., description="Country")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude in decimal degrees")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude in decimal degrees")
    timezone: str = Field(default="UTC", description="IANA timezone name")


class AirportCreate(AirportBase):
    pass


class AirportResponse(AirportBase):
    id: str
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
