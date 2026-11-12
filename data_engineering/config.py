"""Configuration for Data Engineering module."""

from typing import List, Optional, Tuple

# City coordinates matching seed_cities.sql
CITY_COORDINATES = {
    "kuala-lumpur": (3.139000, 101.686855),
    "london": (51.507400, -0.127800),
    "tokyo": (35.689500, 139.691700),
}

# All pilot city codes
PILOT_CITIES = list(CITY_COORDINATES.keys())


def get_city_coordinates(city_code: str) -> Optional[Tuple[float, float]]:
    """Get (latitude, longitude) for a city code."""
    return CITY_COORDINATES.get(city_code)


def get_all_city_codes() -> List[str]:
    """Get all pilot city codes."""
    return PILOT_CITIES.copy()