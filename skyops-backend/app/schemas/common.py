"""Common Pydantic models for API responses."""

from typing import Generic, List, Optional, TypeVar
from pydantic import BaseModel, ConfigDict

T = TypeVar("T")


class APIResponse(BaseModel, Generic[T]):
    """Standardized API envelope."""
    success: bool = True
    data: Optional[T] = None
    message: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class ErrorDetail(BaseModel):
    """Detailed error object."""
    code: str
    message: str
    details: Optional[dict] = None


class ErrorResponse(BaseModel):
    """Standardized error response payload."""
    success: bool = False
    error: ErrorDetail
