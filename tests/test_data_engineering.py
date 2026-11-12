"""Unit and integration tests for Data Engineering Open-Meteo client and pipeline."""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from data_engineering.open_meteo_client import (
    WeatherObservation,
    fetch_current_weather,
    _normalize_response,
    OpenMeteoHTTPError,
    OpenMeteoParseError,
)
from data_engineering.pipeline import (
    IngestionResult,
    upsert_observation,
)


SAMPLE_OPEN_METEO_RESPONSE = {
    "latitude": 3.13,
    "longitude": 101.69,
    "generationtime_ms": 0.123,
    "utc_offset_seconds": 0,
    "timezone": "UTC",
    "timezone_abbreviation": "UTC",
    "elevation": 20.0,
    "current_weather": {
        "temperature": 32.5,
        "windspeed": 10.2,
        "winddirection": 140.0,
        "weathercode": 1,
        "is_day": 1,
        "time": "2026-11-12T12:00"
    },
    "hourly": {
        "time": ["2026-11-12T12:00:00Z"],
        "temperature_2m": [32.5],
        "relative_humidity_2m": [78.0],
        "precipitation": [0.0],
        "wind_speed_10m": [10.2]
    }
}


def test_normalize_response_success():
    """Test successful normalization of Open-Meteo response."""
    observations = _normalize_response("kuala-lumpur", SAMPLE_OPEN_METEO_RESPONSE)
    
    assert len(observations) == 4
    
    # Check temperature
    temp_obs = next(o for o in observations if o.indicator_code == "temperature")
    assert temp_obs.city_id == "kuala-lumpur"
    assert temp_obs.value == 32.5
    assert temp_obs.observed_at == datetime(2026, 11, 12, 12, 0, tzinfo=timezone.utc)
    assert temp_obs.raw_payload["source"] == "open_meteo"
    assert temp_obs.raw_payload["variable"] == "temperature_2m"

    # Check humidity
    hum_obs = next(o for o in observations if o.indicator_code == "humidity")
    assert hum_obs.value == 78.0


def test_normalize_response_missing_hourly():
    """Test normalization fails when hourly time is missing."""
    invalid_data = {"current_weather": {}, "hourly": {}}
    with pytest.raises(OpenMeteoParseError, match="No hourly time data"):
        _normalize_response("kuala-lumpur", invalid_data)


def test_normalize_response_null_values():
    """Test normalization handles null values gracefully (skips them)."""
    data_with_null = {
        "hourly": {
            "time": ["2026-11-12T12:00:00Z"],
            "temperature_2m": [None],
            "relative_humidity_2m": [78.0],
            "precipitation": [0.0],
            "wind_speed_10m": [10.2]
        }
    }
    observations = _normalize_response("kuala-lumpur", data_with_null)
    # temperature_2m should be skipped due to None value
    assert len(observations) == 3
    assert not any(o.indicator_code == "temperature" for o in observations)


@pytest.mark.asyncio
async def test_fetch_current_weather_mock_success():
    """Test fetch_current_weather with mocked httpx client success."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = SAMPLE_OPEN_METEO_RESPONSE

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        observations = await fetch_current_weather("kuala-lumpur")
        
        assert len(observations) == 4
        mock_get.assert_called_once()
        args, kwargs = mock_get.call_args
        assert "api.open-meteo.com" in args[0]
        assert kwargs["params"]["latitude"] == 3.139000


@pytest.mark.asyncio
async def test_fetch_current_weather_http_error():
    """Test fetch_current_weather raises OpenMeteoHTTPError on 500 status."""
    mock_response = MagicMock()
    mock_response.status_code = 500
    mock_response.text = "Internal Server Error"

    with patch("httpx.AsyncClient.get", new_callable=AsyncMock) as mock_get:
        mock_get.return_value = mock_response
        with pytest.raises(OpenMeteoHTTPError, match="Open-Meteo HTTP 500"):
            await fetch_current_weather("kuala-lumpur")


@pytest.mark.asyncio
async def test_upsert_observation_duplicate_handling():
    """Test upsert_observation detects duplicates using unique constraint conditions."""
    mock_session = AsyncMock()
    
    # Mock city lookup
    mock_city = MagicMock()
    mock_city.id = "city-uuid-1"
    
    # Mock indicator lookup
    mock_indicator = MagicMock()
    mock_indicator.id = "ind-uuid-1"
    
    # Mock existing observation query result (found -> duplicate)
    mock_existing_result = MagicMock()
    mock_existing_result.scalar_one_or_none.return_value = MagicMock() # Exists
    
    # Setup session.execute returns: 1. city, 2. indicator, 3. existing check
    mock_session.execute.side_effect = [
        MagicMock(scalar_one_or_none=lambda: mock_city),
        MagicMock(scalar_one_or_none=lambda: mock_indicator),
        mock_existing_result,
    ]
    
    obs = WeatherObservation(
        city_id="kuala-lumpur",
        indicator_code="temperature",
        observed_at=datetime(2026, 11, 12, 12, 0, tzinfo=timezone.utc),
        value=32.5,
        raw_payload={},
    )
    
    inserted = await upsert_observation(mock_session, obs)
    assert inserted is False  # Skipped because duplicate exists
    mock_session.add.assert_not_called()
