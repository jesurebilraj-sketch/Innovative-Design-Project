"""Pydantic schemas for gates and gate availability checks."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


class GateBase(BaseModel):
    airport_id: str
    gate_code: str = Field(..., description="Alphanumeric gate identifier, e.g. B12")
    terminal: str = Field(..., description="Terminal identifier")
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    aircraft_size_limit: str = Field(default="NARROW_BODY", description="REGIONAL, NARROW_BODY, or WIDE_BODY")
    is_active: bool = True


class GateResponse(GateBase):
    id: str
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class GateAvailabilityCheckRequest(BaseModel):
    """Request payload to verify if a gate is free during an interval."""
    gate_id: str
    start_time: datetime = Field(..., description="UTC start of requested occupancy")
    end_time: datetime = Field(..., description="UTC end of requested occupancy")
    aircraft_size: Optional[str] = Field(default="NARROW_BODY", description="Size category of requesting aircraft")


class GateAvailabilityResponse(BaseModel):
    """Result of gate availability and conflict check."""
    gate_id: str
    is_available: bool
    is_compatible: bool
    has_conflict: bool
    reason: str
    conflicting_flight_ids: List[str] = []
