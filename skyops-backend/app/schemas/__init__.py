"""Schemas module exports."""

from app.schemas.common import APIResponse, ErrorDetail, ErrorResponse
from app.schemas.airport import AirportBase, AirportCreate, AirportResponse
from app.schemas.gate import (
    GateBase,
    GateResponse,
    GateAvailabilityCheckRequest,
    GateAvailabilityResponse,
    GateRecommendationRequest,
    GateRecommendationResponse,
)
from app.schemas.flight import (
    FlightBase,
    FlightCreate,
    FlightResponse,
    FlightDetailResponse,
    TurnaroundLegResponse,
    PropagatedLegResponse,
    DelayPropagationResponse,
)
from app.schemas.weather import WeatherBase, WeatherResponse, WeatherSnapshot
from app.schemas.prediction import PredictionRequest, PredictionResponse
from app.schemas.analytics import (
    FlightDelayAnalyticsResponse,
    PredictionAnalyticsResponse,
    GateAnalyticsResponse,
)

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
    "GateRecommendationRequest",
    "GateRecommendationResponse",
    "FlightBase",
    "FlightCreate",
    "FlightResponse",
    "FlightDetailResponse",
    "TurnaroundLegResponse",
    "PropagatedLegResponse",
    "DelayPropagationResponse",
    "WeatherBase",
    "WeatherResponse",
    "WeatherSnapshot",
    "PredictionRequest",
    "PredictionResponse",
    "FlightDelayAnalyticsResponse",
    "PredictionAnalyticsResponse",
    "GateAnalyticsResponse",
]
