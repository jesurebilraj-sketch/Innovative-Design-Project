"""Predictions API endpoint stubs for Phase 3."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/status")
def predictions_status():
    """Status endpoint for predictions module."""
    return {"status": "available", "phase": "phase_3_ready"}
