"""Flight API endpoints."""

from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.flight import FlightDetailResponse, FlightResponse, TurnaroundLegResponse
from app.services.flight_service import FlightService

router = APIRouter()


@router.get("/", response_model=List[FlightResponse], summary="List flights")
def list_flights(
    airport_id: Optional[str] = Query(None, description="Filter by origin or destination airport ID"),
    airline_code: Optional[str] = Query(None, description="Filter by airline code (e.g. KL)"),
    status: Optional[str] = Query(None, description="Filter by status (SCHEDULED, EN_ROUTE, LANDED, DELAYED)"),
    start_time: Optional[datetime] = Query(None, description="Filter departures after UTC timestamp"),
    end_time: Optional[datetime] = Query(None, description="Filter departures before UTC timestamp"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Retrieve flights with optional airport, airline, status, and temporal filtering."""
    service = FlightService(db)
    return service.list_flights(
        airport_id=airport_id,
        airline_code=airline_code,
        status=status,
        start_time=start_time,
        end_time=end_time,
        skip=skip,
        limit=limit,
    )


@router.get("/{flight_id}", response_model=FlightDetailResponse, summary="Get flight details")
def get_flight(
    flight_id: str,
    db: Session = Depends(get_db),
):
    """Retrieve detailed operational flight record including origin and destination aerodromes."""
    service = FlightService(db)
    return service.get_flight(flight_id)


@router.get("/{flight_id}/turnaround", response_model=TurnaroundLegResponse, summary="Get turnaround leg")
def get_turnaround_leg(
    flight_id: str,
    minimum_turnaround_minutes: Optional[int] = Query(None, ge=15, le=180, description="Optional custom turnaround buffer in minutes"),
    db: Session = Depends(get_db),
):
    """Identify the next departure leg for the arriving aircraft at the destination airport.
    
    Applies pure domain turnaround logic per GEMINI_BACKEND.md Section 16.
    """
    service = FlightService(db)
    return service.get_turnaround_leg(
        flight_id=flight_id,
        minimum_turnaround_minutes=minimum_turnaround_minutes,
    )
