"""Airport API endpoints."""

from typing import List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.airport import AirportResponse
from app.schemas.gate import GateResponse
from app.services.airport_service import AirportService

router = APIRouter()


@router.get("/", response_model=List[AirportResponse], summary="List airports")
def list_airports(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Retrieve all registered aerodromes."""
    service = AirportService(db)
    return service.list_airports(skip=skip, limit=limit)


@router.get("/{airport_id}", response_model=AirportResponse, summary="Get airport details")
def get_airport(
    airport_id: str,
    db: Session = Depends(get_db),
):
    """Retrieve airport details by UUID or 3-letter IATA code."""
    service = AirportService(db)
    return service.get_airport(airport_id)


@router.get("/{airport_id}/gates", response_model=List[GateResponse], summary="List airport gates")
def list_airport_gates(
    airport_id: str,
    db: Session = Depends(get_db),
):
    """Retrieve all active gates located at the specified aerodrome."""
    service = AirportService(db)
    return service.list_airport_gates(airport_id)
