"""Schemas module exports."""

from app.schemas.common import APIResponse, ErrorDetail, ErrorResponse
from app.schemas.airport import AirportBase, AirportCreate, AirportResponse
from app.schemas.gate import GateBase, GateResponse, GateAvailabilityCheckRequest, GateAvailabilityResponse
from app.schemas.flight import FlightBase, FlightCreate, FlightResponse, FlightDetailResponse, TurnaroundLegResponse
from app.schemas.weather import WeatherBase, WeatherResponse, WeatherSnapshot

__all__ = [
    "APIResponse",
    "ErrorDetail",
    "ErrorResponse",
    "AirportBase",
    "AirportCreate",
    "AirportResponse",
    "GateBase",
    "GateResponse",
    "GateAvailabilityCheckRequest",
    "GateAvailabilityResponse",
    "FlightBase",
    "FlightCreate",
    "FlightResponse",
    "FlightDetailResponse",
    "TurnaroundLegResponse",
    "WeatherBase",
    "WeatherResponse",
    "WeatherSnapshot",
]
