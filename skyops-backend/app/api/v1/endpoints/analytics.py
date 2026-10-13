"""Analytics API endpoints for operational metrics and history."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.analytics import (
    FlightDelayAnalyticsResponse,
    PredictionAnalyticsResponse,
    GateAnalyticsResponse,
)
from app.services.analytics import AnalyticsService

router = APIRouter()


@router.get("/status")
def analytics_status():
    """Status endpoint for analytics module."""
    return {"status": "available", "phase": "phase_4_ready"}


@router.get("/delays", response_model=FlightDelayAnalyticsResponse, summary="Get flight delay statistics")
def get_flight_delay_analytics_endpoint(
    db: Session = Depends(get_db),
):
    """Retrieve aggregate statistics on flight delays, on-time rates, and status distributions."""
    service = AnalyticsService(db)
    return service.get_flight_delay_analytics()


@router.get("/predictions", response_model=PredictionAnalyticsResponse, summary="Get ML prediction analytics")
def get_prediction_analytics_endpoint(
    db: Session = Depends(get_db),
):
    """Retrieve aggregate statistics on ML predictions, model versions, and delay classifications."""
    service = AnalyticsService(db)
    return service.get_prediction_analytics()


@router.get("/gates", response_model=GateAnalyticsResponse, summary="Get gate utilization and conflicts analytics")
def get_gate_analytics_endpoint(
    db: Session = Depends(get_db),
):
    """Retrieve aggregate statistics on gate utilization, assignment types, and conflict resolutions."""
    service = AnalyticsService(db)
    return service.get_gate_analytics()
