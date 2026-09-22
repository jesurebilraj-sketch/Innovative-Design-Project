"""Domain port protocols defining external integration boundaries.

Research Basis:
- Model-agnostic predictor interface per GEMINI_BACKEND.md Section 21.
- Keeps pure domain and service logic decoupled from machine learning libraries (CatBoost, XGBoost, etc.)
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Mapping, Optional, Protocol
from app.schemas.weather import WeatherSnapshot


@dataclass(frozen=True)
class DelayPrediction:
    """Domain representation of a flight delay prediction output."""
    model_name: str
    model_version: str
    delayed_probability: float
    predicted_delay_minutes: float
    prediction_class: str
    generated_at: datetime
    input_snapshot: Optional[Mapping[str, Any]] = None


class DelayPredictor(Protocol):
    """Protocol that any ML or rule-based delay predictor must implement."""

    def predict(self, features: Mapping[str, Any]) -> DelayPrediction:
        """Evaluate flight delay from an operational feature snapshot."""
        ...


class WeatherProvider(Protocol):
    """Protocol for surface weather data providers (e.g. Open-Meteo)."""

    def get_weather(
        self, latitude: float, longitude: float, target_time: datetime
    ) -> Optional[WeatherSnapshot]:
        """Fetch surface weather observations for given coordinates and timestamp."""
        ...
