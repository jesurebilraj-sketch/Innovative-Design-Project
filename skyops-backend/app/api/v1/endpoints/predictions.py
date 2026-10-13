"""Predictions API endpoints."""

from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.prediction import PredictionRequest, PredictionResponse
from app.services.prediction import PredictionService

router = APIRouter()


@router.get("/status")
def predictions_status():
    """Status endpoint for predictions module."""
    return {"status": "available", "phase": "phase_3_ready"}


@router.post("/predict", response_model=PredictionResponse, summary="Predict flight delay")
def predict_flight_delay_endpoint(
    request: PredictionRequest,
    db: Session = Depends(get_db),
):
    """Generate flight delay prediction and persist inference results for auditing."""
    service = PredictionService(db)
    return service.predict_flight_delay(request)


@router.get("/flight/{flight_id}", response_model=List[PredictionResponse], summary="Get flight prediction history")
def get_flight_predictions_endpoint(
    flight_id: str,
    db: Session = Depends(get_db),
):
    """Retrieve historical predictions generated for a specific flight record."""
    service = PredictionService(db)
    return service.get_flight_predictions(flight_id)
