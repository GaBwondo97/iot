"""OpenAQ Air Quality API v3 Client for CityPulse AI."""

import logging
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import httpx

from data_engineering.config import get_city_coordinates

log = logging.getLogger(__name__)

OPENAQ_API_URL = "https://api.openaq.org/v3"

# Map OpenAQ parameters to our indicator codes
OPENAQ_TO_INDICATOR = {
    "pm25": "pm25",
    "pm10": "pm10",
}

# Expected units from OpenAQ (standard units)
EXPECTED_UNITS = {
    "pm25": "µg/m³",
    "pm10": "µg/m³",
}


@dataclass
class AirQualityObservation:
    """Normalized air quality observation ready for database insertion."""
    city_id: str
    indicator_code: str
    observed_at: datetime
    value: float
    raw_payload: Dict[str, Any]


class OpenAQError(Exception):
    """Base exception for OpenAQ client errors."""
    pass


class OpenAQHTTPError(OpenAQError):
    """HTTP error from OpenAQ API."""
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        super().__init__(f"OpenAQ HTTP {status_code}: {message}")


class OpenAQParseError(OpenAQError):
    """Failed to parse OpenAQ response."""
    pass


class OpenAQAuthError(OpenAQError):
    """Authentication error (missing/invalid API key)."""
    pass


def _get_openaq_api_key() -> Optional[str]:
    """Get OpenAQ API key from environment."""
    return os.environ.get("OPENAQ_API_KEY")


async def find_nearest_location(
    city_code: str,
    timeout: float = 10.0,
) -> Optional[Dict[str, Any]]:
    """
    Find the nearest OpenAQ monitoring location for a city.
    
    Returns location metadata or None if no suitable location found.
    """
    coords = get_city_coordinates(city_code)
    if not coords:
        log.warning(f"Unknown city code: {city_code}")
        return None
    
    lat, lon = coords
    
    params = {
        "coordinates": f"{lat},{lon}",
        "radius": 50000,  # 50km radius
        "order_by": "distance",
        "limit": 1,
    }
    
    api_key = _get_openaq_api_key()
    headers = {}
    if api_key:
        headers["X-API-Key"] = api_key
    
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            response = await client.get(
                f"{OPENAQ_API_URL}/locations",
                params=params,
                headers=headers,
            )
        except httpx.TimeoutException as e:
            raise OpenAQHTTPError(408, f"Request timeout: {e}")
        except httpx.RequestError as e:
            raise OpenAQHTTPError(0, f"Request failed: {e}")
    
    if response.status_code == 401:
        raise OpenAQAuthError("Invalid or missing API key")
    if response.status_code == 429:
        raise OpenAQHTTPError(429, "Rate limit exceeded")
    if response.status_code != 200:
        raise OpenAQHTTPError(response.status_code, response.text)
    
    try:
        data = response.json()
    except ValueError as e:
        raise OpenAQParseError(f"Invalid JSON response: {e}")
    
    results = data.get("results", [])
    if not results:
        log.warning(f"No OpenAQ monitoring locations found near {city_code}")
        return None
    
    location = results[0]
    distance_km = location.get("distance", 0) / 1000.0
    log.info(f"Found OpenAQ location for {city_code}: {location.get('name')} "
             f"({distance_km:.1f} km away)")
    
    return location


async def fetch_latest_measurements(
    location_id: int,
    city_code: str,
    timeout: float = 10.0,
) -> List[AirQualityObservation]:
    """
    Fetch latest measurements for a specific OpenAQ location.
    
    Args:
        location_id: OpenAQ location ID
        city_code: Our city code for reference
        timeout: Request timeout in seconds
        
    Returns:
        List of normalized AirQualityObservation objects
    """
    params = {
        "location_id": location_id,
        "limit": 100,
        "order_by": "datetime",
        "sort": "desc",
    }
    
    api_key = _get_openaq_api_key()
    headers = {}
    if api_key:
        headers["X-API-Key"] = api_key
    
    async with httpx.AsyncClient(timeout=timeout) as client:
        try:
            response = await client.get(
                f"{OPENAQ_API_URL}/measurements",
                params=params,
                headers=headers,
            )
        except httpx.TimeoutException as e:
            raise OpenAQHTTPError(408, f"Request timeout: {e}")
        except httpx.RequestError as e:
            raise OpenAQHTTPError(0, f"Request failed: {e}")
    
    if response.status_code == 401:
        raise OpenAQAuthError("Invalid or missing API key")
    if response.status_code == 429:
        raise OpenAQHTTPError(429, "Rate limit exceeded")
    if response.status_code != 200:
        raise OpenAQHTTPError(response.status_code, response.text)
    
    try:
        data = response.json()
    except ValueError as e:
        raise OpenAQParseError(f"Invalid JSON response: {e}")
    
    return _normalize_measurements(city_code, data, location_id)


def _normalize_measurements(
    city_code: str,
    data: Dict[str, Any],
    location_id: int,
) -> List[AirQualityObservation]:
    """Normalize OpenAQ measurements response to AirQualityObservation objects."""
    observations = []
    
    results = data.get("results", [])
    if not results:
        log.warning(f"No measurements found for location {location_id}")
        return observations
    
    # Group by parameter and take the most recent measurement for each
    latest_by_param = {}
    for item in results:
        param = item.get("parameter")
        if param not in OPENAQ_TO_INDICATOR:
            continue
        
        if param not in latest_by_param:
            latest_by_param[param] = item
    
    for param, item in latest_by_param.items():
        indicator_code = OPENAQ_TO_INDICATOR[param]
        value = item.get("value")
        if value is None:
            log.warning(f"Null value for {param} in city {city_code}")
            continue
        
        # Parse timestamp
        datetime_str = item.get("datetime", {}).get("utc")
        if not datetime_str:
            log.warning(f"Missing datetime for {param} in city {city_code}")
            continue
        
        try:
            observed_at = datetime.fromisoformat(datetime_str.replace("Z", "+00:00"))
            if observed_at.tzinfo is None:
                observed_at = observed_at.replace(tzinfo=timezone.utc)
        except ValueError as e:
            log.warning(f"Invalid timestamp format for {param}: {datetime_str}")
            continue
        
        # Build raw payload for audit
        raw_payload = {
            "source": "openaq",
            "parameter": param,
            "unit": item.get("unit"),
            "city_code": city_code,
            "location_id": location_id,
            "location_name": item.get("location"),
            "coordinates": item.get("coordinates"),
            "attribution": item.get("attribution"),
            "source_name": item.get("sourceName"),
        }
        
        observations.append(AirQualityObservation(
            city_id=city_code,
            indicator_code=indicator_code,
            observed_at=observed_at,
            value=float(value),
            raw_payload=raw_payload,
        ))
    
    return observations


async def fetch_city_air_quality(
    city_code: str,
    timeout: float = 10.0,
) -> List[AirQualityObservation]:
    """
    Fetch latest air quality measurements for a city.
    
    Returns empty list if no monitoring station is available.
    """
    location = await find_nearest_location(city_code, timeout)
    if not location:
        return []
    
    location_id = location.get("id")
    if not location_id:
        log.warning(f"Location found but missing ID for {city_code}")
        return []
    
    return await fetch_latest_measurements(location_id, city_code, timeout)