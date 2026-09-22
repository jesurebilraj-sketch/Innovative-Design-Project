"""Analytics API endpoint stubs for Phase 4."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/status")
def analytics_status():
    """Status endpoint for analytics module."""
    return {"status": "available", "phase": "phase_4_ready"}
