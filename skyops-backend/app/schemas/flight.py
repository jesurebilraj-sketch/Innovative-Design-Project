"""Pydantic schemas for flights and operational turnarounds."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.airport import AirportResponse


class FlightBase(BaseModel):
    flight_number: str = Field(..., description="Flight number, e.g. KL1234")
    airline_code: str = Field(..., description="Airline IATA code, e.g. KL")
    aircraft_id: Optional[str] = Field(None, description="Aircraft tail number / registration")
    origin_airport_id: str
    destination_airport_id: str
    scheduled_departure: datetime
    scheduled_arrival: datetime
    actual_departure: Optional[datetime] = None
    actual_arrival: Optional[datetime] = None
    status: str = Field(default="SCHEDULED", description="SCHEDULED, EN_ROUTE, LANDED, DELAYED, CANCELLED, DIVERTED")
    cancelled: bool = False
    diverted: bool = False
    passenger_count: Optional[int] = None
    block_time_minutes: Optional[int] = None


class FlightCreate(FlightBase):
    pass


class FlightResponse(FlightBase):
    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class FlightDetailResponse(FlightResponse):
    origin_airport: Optional[AirportResponse] = None
    destination_airport: Optional[AirportResponse] = None


class TurnaroundLegResponse(BaseModel):
    """Schema describing turnaround pairing between incoming arrival and next departure."""
    arriving_flight_id: str
    arriving_flight_number: str
    departing_flight_id: Optional[str] = None
    departing_flight_number: Optional[str] = None
    aircraft_id: Optional[str] = None
    airport_id: str
    arrival_time: datetime
    scheduled_departure_time: Optional[datetime] = None
    turnaround_buffer_minutes: Optional[float] = None
    minimum_required_minutes: int
    is_feasible: bool
    status: str = Field(..., description="MATCHED, NO_SUBSEQUENT_LEG, or INVALID_AIRCRAFT")
