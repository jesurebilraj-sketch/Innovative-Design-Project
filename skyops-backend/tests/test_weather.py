"""Test Weather API and Open-Meteo integration."""

from datetime import datetime, timezone
from unittest.mock import patch, MagicMock
from app.integrations.weather import OpenMeteoClient
from app.schemas.weather import WeatherSnapshot


def test_get_airport_weather_endpoint(client, seed_data):
    """Verify weather endpoint returns structured weather for an aerodrome."""
    response = client.get("/api/v1/weather/airport/apt-rtm")
    assert response.status_code == 200
    data = response.json()
    assert data["airport_id"] == "apt-rtm"
    assert "temperature_c" in data
    assert "wind_speed_mps" in data


def test_get_airport_weather_unknown_airport(client, seed_data):
    """Verify 404 response for unknown airport."""
    response = client.get("/api/v1/weather/airport/unknown-airport-id")
    assert response.status_code == 404
    data = response.json()
    assert data["error"]["code"] == "AIRPORT_NOT_FOUND"


def test_open_meteo_client_resilience_on_network_failure():
    """Verify OpenMeteoClient returns None instead of raising unhandled exception on network error."""
    client = OpenMeteoClient(base_url="https://invalid-non-existent-domain.test", timeout=1.0)
    result = client.get_weather(
        latitude=52.3,
        longitude=4.7,
        target_time=datetime.now(timezone.utc),
    )
    assert result is None
