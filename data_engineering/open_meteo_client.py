"""Open-Meteo Weather API Client for CityPulse AI."""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx

from data_engineering.config import get_city_coordinates

log = logging.getLogger(__name__)

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

# Map Open-Meteo variables to our indicator codes
OPEN_METEO_TO_INDICATOR = {
    "temperature_2m": "temperature",
    "relative_humidity_2m": "humidity",
    "precipitation": "rainfall",
    "wind_speed_10m": "wind_speed",
}

# Expected units from Open-Meteo
EXPECTED_UNITS = {
    "temperature_2m": "celsius",
    "relative_humidity_2m": "percent",
    "precipitation": "mm",
    "wind_speed_10m": "kmh",
}


@dataclass
class WeatherObservation:
    """Normalized weather observation ready for database insertion."""
    city_id: str
    indicator_code: str
    observed_at: datetime
    value: float
    raw_payload: Dict[str, Any]


class OpenMeteoError(Exception):
    """Base exception for Open-Meteo client errors."""
    pass


class OpenMeteoHTTPError(OpenMeteoError):
    """HTTP error from Open-Meteo API."""
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        super().__init__(f"Open-Meteo HTTP {status_code}: {message}")


class OpenMeteoParseError(OpenMeteoError):
    """Failed to parse Open-Meteo response."""
    pass


async def fetch_current_weather(
    city_code: str,
    timeout: float = 10.0,
) -> List[WeatherObservation]:
    """
    Fetch current weather for a city from Open-Meteo.
    
    Args:
        city_code: City code (kuala-lumpur, london, tokyo)
        timeout: Request timeout in seconds
        
    Returns:
        List of normalized WeatherObservation objects
        
    Raises:
        OpenMeteoHTTPError: On HTTP error or non-200 response
        OpenMeteoParseError: On invalid/missing response data
    """
    coords = get_city_coordinates(city_code)
    if not coords:
        raise OpenMeteoParseError(f"Unknown city code: {city_code}")
    
    lat, lon = coords
    
    params = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": "true",
        "hourly": ",".join(OPEN_METEO_TO_INDICATOR.keys()),
        "timezone": "UTC",
        "forecast_hours": 1,
    }
    
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            response = await client.get(OPEN_METEO_URL, params=params)
        except httpx.TimeoutException as e:
            raise OpenMeteoHTTPError(408, f"Request timeout: {e}")
        except httpx.RequestError as e:
            raise OpenMeteoHTTPError(0, f"Request failed: {e}")
    
    if response.status_code != 200:
        raise OpenMeteoHTTPError(response.status_code, response.text)
    
    try:
        data = response.json()
    except ValueError as e:
        raise OpenMeteoParseError(f"Invalid JSON response: {e}")
    
    return _normalize_response(city_code, data)


def _normalize_response(
    city_code: str,
    data: Dict[str, Any],
) -> List[WeatherObservation]:
    """Normalize Open-Meteo response to WeatherObservation objects."""
    observations = []
    
    # Get current weather (single point) and hourly (array)
    current = data.get("current_weather", {})
    hourly = data.get("hourly", {})
    hourly_times = hourly.get("time", [])
    
    if not hourly_times:
        raise OpenMeteoParseError("No hourly time data in response")
    
    # Use the first hourly timestamp (current hour)
    observed_at_str = hourly_times[0]
    try:
        observed_at = datetime.fromisoformat(observed_at_str.replace("Z", "+00:00"))
        if observed_at.tzinfo is None:
            observed_at = observed_at.replace(tzinfo=timezone.utc)
    except ValueError as e:
        raise OpenMeteoParseError(f"Invalid timestamp format: {observed_at_str}")
    
    # Map each indicator
    for api_var, indicator_code in OPEN_METEO_TO_INDICATOR.items():
        values = hourly.get(api_var, [])
        if not values:
            log.warning(f"No data for {api_var} in city {city_code}")
            continue
        
        value = values[0]
        if value is None:
            log.warning(f"Null value for {api_var} in city {city_code}")
            continue
        
        # Build raw payload for audit
        raw_payload = {
            "source": "open_meteo",
            "variable": api_var,
            "unit": EXPECTED_UNITS.get(api_var),
            "city_code": city_code,
            "latitude": data.get("latitude"),
            "longitude": data.get("longitude"),
            "generationtime_ms": data.get("generationtime_ms"),
            "utc_offset_seconds": data.get("utc_offset_seconds"),
        }
        
        observations.append(WeatherObservation(
            city_id=city_code,
            indicator_code=indicator_code,
            observed_at=observed_at,
            value=float(value),
            raw_payload=raw_payload,
        ))
    
    return observations