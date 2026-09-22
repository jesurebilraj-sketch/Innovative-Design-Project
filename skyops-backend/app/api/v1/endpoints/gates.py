"""Gate API endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.schemas.gate import GateAvailabilityCheckRequest, GateAvailabilityResponse
from app.services.gate_recommendation import GateService

router = APIRouter()


@router.post("/check-availability", response_model=GateAvailabilityResponse, summary="Check gate availability")
def check_gate_availability_endpoint(
    request: GateAvailabilityCheckRequest,
    db: Session = Depends(get_db),
):
    """Verify whether a gate is available without conflicts during a requested interval.
    
    Applies pure domain half-open interval overlap checking and aircraft size compatibility.
    """
    service = GateService(db)
    return service.check_availability(request)
