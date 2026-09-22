"""Predictor adapter and rule-based fallback implementation.

Research Basis:
- Sternberg et al. (2017) & Huo et al. (2020):
  Delay estimation requires temporal, spatial, and weather feature signals.
- GEMINI_BACKEND.md Section 21 & 44:
  Model-agnostic adapter ensuring the backend operates consistently with CatBoost or fallback stubs.
"""

from datetime import datetime, timezone
from typing import Any, Mapping, Optional
import httpx
from app.core.exceptions import InvalidPredictionError, PredictorUnavailableError
from app.core.settings import settings
from app.domain.ports import DelayPrediction, DelayPredictor


class RuleBasedPredictorStub(DelayPredictor):
    """Deterministic, research-grounded fallback predictor stub.
    
    Ensures the backend remains operational and testable without requiring
    an active ML inference microservice.
    """

    def __init__(self, model_name: str = "skyops-heuristic-stub", model_version: str = "v1.0.0"):
        self.model_name = model_name
        self.model_version = model_version

    def predict(self, features: Mapping[str, Any]) -> DelayPrediction:
        """Estimate flight delay probability and duration based on feature heuristics."""
        # Baseline probability: 0.15
        prob = 0.15
        delay_minutes = 0.0

        # Feature signals
        rain = features.get("rain_mm", 0.0) or 0.0
        wind = features.get("wind_speed_mps", 0.0) or 0.0
        vis = features.get("visibility_km", 10.0) or 10.0
        dep_hour = features.get("departure_hour", 12) or 12

        # Adverse weather adjustments
        if rain > 5.0:
            prob += 0.35
            delay_minutes += 25.0
        elif rain > 1.0:
            prob += 0.15
            delay_minutes += 12.0

        if wind > 15.0:
            prob += 0.25
            delay_minutes += 20.0

        if vis < 3.0:
            prob += 0.20
            delay_minutes += 15.0

        # Evening congestion effect (17:00 - 21:00)
        if 17 <= dep_hour <= 21:
            prob += 0.10
            delay_minutes += 10.0

        # Clamp probability to [0.0, 0.99]
        prob = min(max(prob, 0.0), 0.99)
        delay_minutes = max(delay_minutes, 0.0)
        classification = "DELAYED" if prob >= 0.50 else "ON_TIME"

        return DelayPrediction(
            model_name=self.model_name,
            model_version=self.model_version,
            delayed_probability=round(prob, 4),
            predicted_delay_minutes=round(delay_minutes, 1),
            prediction_class=classification,
            generated_at=datetime.now(timezone.utc),
            input_snapshot=dict(features),
        )


class HttpPredictorClient(DelayPredictor):
    """Client adapter connecting to an external ML prediction microservice."""

    def __init__(
        self,
        service_url: str = settings.PREDICTOR_SERVICE_URL,
        fallback_stub: Optional[DelayPredictor] = None,
    ):
        self.service_url = service_url
        self.fallback = fallback_stub or RuleBasedPredictorStub()

    def predict(self, features: Mapping[str, Any]) -> DelayPrediction:
        """Call external prediction service with automatic fallback."""
        try:
            with httpx.Client(timeout=5.0) as client:
                resp = client.post(f"{self.service_url}/predict", json=dict(features))
                if resp.status_code == 200:
                    data = resp.json()
                    prob = float(data["delayed_probability"])
                    delay = float(data["predicted_delay_minutes"])
                    if not (0.0 <= prob <= 1.0):
                        raise InvalidPredictionError(f"Probability {prob} out of bounds [0, 1]")
                    return DelayPrediction(
                        model_name=data.get("model_name", "external-catboost"),
                        model_version=data.get("model_version", "1.0"),
                        delayed_probability=prob,
                        predicted_delay_minutes=delay,
                        prediction_class=data.get("prediction_class", "DELAYED" if prob >= 0.5 else "ON_TIME"),
                        generated_at=datetime.now(timezone.utc),
                        input_snapshot=dict(features),
                    )
        except Exception:
            # Fall back to deterministic stub per decision-support resilience
            pass

        return self.fallback.predict(features)


def get_predictor() -> DelayPredictor:
    """Return the active predictor adapter."""
    return HttpPredictorClient()
