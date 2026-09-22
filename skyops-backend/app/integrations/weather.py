"""Open-Meteo weather integration adapter.

Research Basis:
- Zoutendijk & Mitici (2021) & Prasanna et al. (2026): External weather variables
  (temperature, rain, visibility, wind speed, pressure, cloud cover) provide critical
  context for operational disruptions and flight delay prediction.
"""

from datetime import datetime, timezone
from typing import Any, Dict, Optional
import httpx
from app.core.exceptions import WeatherProviderError
from app.core.settings import settings
from app.domain.ports import WeatherProvider
from app.schemas.weather import WeatherSnapshot


class OpenMeteoClient(WeatherProvider):
    """Client adapter for retrieving surface weather from Open-Meteo."""

    def __init__(
        self,
        base_url: str = settings.OPEN_METEO_BASE_URL,
        timeout: float = settings.WEATHER_TIMEOUT_SECONDS,
    ):
        self.base_url = base_url
        self.timeout = timeout

    def get_weather(
        self, latitude: float, longitude: float, target_time: datetime
    ) -> Optional[WeatherSnapshot]:
        """Fetch surface weather metrics for the specified location and time.
        
        Requests hourly parameters and finds the record closest to target_time.
        Returns None gracefully if the service is unreachable, logging the issue.
        """
        params = {
            "latitude": latitude,
            "longitude": longitude,
            "hourly": [
                "temperature_2m",
                "precipitation",
                "rain",
                "visibility",
                "wind_speed_10m",
                "wind_direction_10m",
                "surface_pressure",
                "cloud_cover",
            ],
            "wind_speed_unit": "ms",
            "timeformat": "iso8601",
        }

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(self.base_url, params=params)
                if response.status_code != 200:
                    return None
                data = response.json()
        except Exception:
            # Operational resilience per GEMINI_BACKEND.md Section 22:
            # Do not crash the application when external weather is temporarily unreachable.
            return None

        hourly = data.get("hourly", {})
        times = hourly.get("time", [])
        if not times:
            return None

        # Parse timestamps and find index closest to target_time
        target_iso = target_time.strftime("%Y-%m-%dT%H:00")
        best_idx = 0
        if target_iso in times:
            best_idx = times.index(target_iso)
        else:
            # Find closest hour
            def time_diff_key(idx: int) -> float:
                try:
                    dt = datetime.fromisoformat(times[idx]).replace(tzinfo=timezone.utc)
                    return abs((dt - target_time).total_seconds())
                except Exception:
                    return float("inf")

            best_idx = min(range(len(times)), key=time_diff_key)

        # Extract values
        temp = hourly.get("temperature_2m", [None])[best_idx]
        precip = hourly.get("precipitation", [None])[best_idx]
        rain = hourly.get("rain", [None])[best_idx]
        vis_raw = hourly.get("visibility", [None])[best_idx]
        vis_km = (vis_raw / 1000.0) if (vis_raw is not None) else None
        wind_spd = hourly.get("wind_speed_10m", [None])[best_idx]
        wind_dir = hourly.get("wind_direction_10m", [None])[best_idx]
        pressure = hourly.get("surface_pressure", [None])[best_idx]
        clouds = hourly.get("cloud_cover", [None])[best_idx]

        return WeatherSnapshot(
            observed_at=target_time,
            temperature_c=temp,
            precipitation_mm=precip,
            rain_mm=rain,
            visibility_km=vis_km,
            wind_speed_mps=wind_spd,
            wind_direction_deg=wind_dir,
            pressure_hpa=pressure,
            cloud_cover_pct=clouds,
            source="open-meteo",
        )
