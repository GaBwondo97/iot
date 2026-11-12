"""Unit and integration tests for OpenAQ client and air quality pipeline."""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from data_engineering.openaq_client import (
    AirQualityObservation,
    find_nearest_location,
    fetch_latest_measurements,
    fetch_city_air_quality,
    OPENAQ_TO_INDICATOR,
    OpenAQHTTPError,
    OpenAQAuthError,
    OpenAQParseError,
)
from data_engineering.pipeline import (
    upsert_observation,
    IngestionResult,
    ingest_city_air_quality,
)
from app.db.models import Observation


# Sample OpenAQ API responses
SAMPLE_LOCATION_RESPONSE = {
    "results": [
        {
            "id": 12345,
            "name": "Kuala Lumpur Station",
            "coordinates": {"latitude": 3.139, "longitude": 101.687},
            "distance": 2500,
        }
    ]
}

SAMPLE_MEASUREMENTS_RESPONSE = {
    "results": [
        {
            "parameter": "pm25",
            "value": 15.5,
            "unit": "µg/m³",
            "datetime": {"utc": "2026-11-13T10:00:00Z"},
            "location": "Kuala Lumpur Station",
            "coordinates": {"latitude": 3.139, "longitude": 101.687},
            "attribution": "OpenAQ",
            "sourceName": "Department of Environment Malaysia",
        },
        {
            "parameter": "pm10",
            "value": 25.0,
            "unit": "µg/m³",
            "datetime": {"utc": "2026-11-13T10:00:00Z"},
            "location": "Kuala Lumpur Station",
            "coordinates": {"latitude": 3.139, "longitude": 101.687},
            "attribution": "OpenAQ",
            "sourceName": "Department of Environment Malaysia",
        },
    ]
}

SAMPLE_EMPTY_LOCATION_RESPONSE = {"results": []}
SAMPLE_EMPTY_MEASUREMENTS_RESPONSE = {"results": []}


class TestOpenAQClient:
    """Test OpenAQ API client functions."""

    @pytest.mark.asyncio
    async def test_find_nearest_location_success(self):
        """Test successful location discovery."""
        with patch.dict("os.environ", {"OPENAQ_API_KEY": "test-key"}):
            with patch("httpx.AsyncClient.get") as mock_get:
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = SAMPLE_LOCATION_RESPONSE
                mock_get.return_value = mock_response
                
                location = await find_nearest_location("kuala-lumpur")
                
                assert location is not None
                assert location["id"] == 12345
                assert location["name"] == "Kuala Lumpur Station"
                mock_get.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_nearest_location_no_station(self):
        """Test when no monitoring station is available."""
        with patch.dict("os.environ", {"OPENAQ_API_KEY": "test-key"}):
            with patch("httpx.AsyncClient.get") as mock_get:
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = SAMPLE_EMPTY_LOCATION_RESPONSE
                mock_get.return_value = mock_response
                
                location = await find_nearest_location("kuala-lumpur")
                
                assert location is None

    @pytest.mark.asyncio
    async def test_find_nearest_location_auth_error(self):
        """Test authentication error handling."""
        with patch.dict("os.environ", {"OPENAQ_API_KEY": "invalid-key"}):
            with patch("httpx.AsyncClient.get") as mock_get:
                mock_response = MagicMock()
                mock_response.status_code = 401
                mock_response.text = "Unauthorized"
                mock_get.return_value = mock_response
                
                with pytest.raises(OpenAQAuthError):
                    await find_nearest_location("kuala-lumpur")

    @pytest.mark.asyncio
    async def test_find_nearest_location_rate_limit(self):
        """Test rate limit handling."""
        with patch.dict("os.environ", {"OPENAQ_API_KEY": "test-key"}):
            with patch("httpx.AsyncClient.get") as mock_get:
                mock_response = MagicMock()
                mock_response.status_code = 429
                mock_response.text = "Rate limit exceeded"
                mock_get.return_value = mock_response
                
                with pytest.raises(OpenAQHTTPError) as exc:
                    await find_nearest_location("kuala-lumpur")
                assert exc.value.status_code == 429

    @pytest.mark.asyncio
    async def test_find_nearest_location_no_api_key(self):
        """Test request without API key (still works but may be rate limited)."""
        with patch.dict("os.environ", {}, clear=True):
            with patch("httpx.AsyncClient.get") as mock_get:
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = SAMPLE_LOCATION_RESPONSE
                mock_get.return_value = mock_response
                
                location = await find_nearest_location("kuala-lumpur")
                
                assert location is not None
                # Verify no X-API-Key header sent
                call_args = mock_get.call_args
                headers = call_args.kwargs.get("headers", {})
                assert "X-API-Key" not in headers

    @pytest.mark.asyncio
    async def test_fetch_latest_measurements_success(self):
        """Test successful measurement fetch and normalization."""
        with patch.dict("os.environ", {"OPENAQ_API_KEY": "test-key"}):
            with patch("httpx.AsyncClient.get") as mock_get:
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = SAMPLE_MEASUREMENTS_RESPONSE
                mock_get.return_value = mock_response
                
                observations = await fetch_latest_measurements(12345, "kuala-lumpur")
                
                assert len(observations) == 2
                assert all(isinstance(o, AirQualityObservation) for o in observations)
                
                # Check PM2.5
                pm25 = next(o for o in observations if o.indicator_code == "pm25")
                assert pm25.value == 15.5
                assert pm25.city_id == "kuala-lumpur"
                assert pm25.observed_at == datetime(2026, 11, 13, 10, 0, 0, tzinfo=timezone.utc)
                assert pm25.raw_payload["parameter"] == "pm25"
                assert pm25.raw_payload["unit"] == "µg/m³"
                
                # Check PM10
                pm10 = next(o for o in observations if o.indicator_code == "pm10")
                assert pm10.value == 25.0

    @pytest.mark.asyncio
    async def test_fetch_latest_measurements_missing_parameter(self):
        """Test handling of unsupported parameters."""
        response = {
            "results": [
                {
                    "parameter": "o3",  # Not in OPENAQ_TO_INDICATOR
                    "value": 50.0,
                    "unit": "µg/m³",
                    "datetime": {"utc": "2026-11-13T10:00:00Z"},
                }
            ]
        }
        with patch.dict("os.environ", {"OPENAQ_API_KEY": "test-key"}):
            with patch("httpx.AsyncClient.get") as mock_get:
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = response
                mock_get.return_value = mock_response
                
                observations = await fetch_latest_measurements(12345, "kuala-lumpur")
                
                assert len(observations) == 0  # Unsupported parameter filtered out

    @pytest.mark.asyncio
    async def test_fetch_latest_measurements_null_value(self):
        """Test handling of null measurement values."""
        response = {
            "results": [
                {
                    "parameter": "pm25",
                    "value": None,
                    "unit": "µg/m³",
                    "datetime": {"utc": "2026-11-13T10:00:00Z"},
                }
            ]
        }
        with patch.dict("os.environ", {"OPENAQ_API_KEY": "test-key"}):
            with patch("httpx.AsyncClient.get") as mock_get:
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = response
                mock_get.return_value = mock_response
                
                observations = await fetch_latest_measurements(12345, "kuala-lumpur")
                
                assert len(observations) == 0  # Null values skipped

    @pytest.mark.asyncio
    async def test_fetch_latest_measurements_invalid_timestamp(self):
        """Test handling of invalid timestamp format."""
        response = {
            "results": [
                {
                    "parameter": "pm25",
                    "value": 15.5,
                    "unit": "µg/m³",
                    "datetime": {"utc": "invalid-timestamp"},
                }
            ]
        }
        with patch.dict("os.environ", {"OPENAQ_API_KEY": "test-key"}):
            with patch("httpx.AsyncClient.get") as mock_get:
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = response
                mock_get.return_value = mock_response
                
                observations = await fetch_latest_measurements(12345, "kuala-lumpur")
                
                assert len(observations) == 0  # Invalid timestamp skipped

    @pytest.mark.asyncio
    async def test_fetch_city_air_quality_full_flow(self):
        """Test complete city air quality fetch flow."""
        with patch.dict("os.environ", {"OPENAQ_API_KEY": "test-key"}):
            with patch("data_engineering.openaq_client.httpx.AsyncClient.get") as mock_get:
                # First call: find location
                # Second call: fetch measurements
                mock_location_response = MagicMock()
                mock_location_response.status_code = 200
                mock_location_response.json.return_value = SAMPLE_LOCATION_RESPONSE
                
                mock_measurements_response = MagicMock()
                mock_measurements_response.status_code = 200
                mock_measurements_response.json.return_value = SAMPLE_MEASUREMENTS_RESPONSE
                
                mock_get.side_effect = [mock_location_response, mock_measurements_response]
                
                observations = await fetch_city_air_quality("kuala-lumpur")
                
                assert len(observations) == 2
                assert mock_get.call_count == 2

    @pytest.mark.asyncio
    async def test_fetch_city_air_quality_no_location(self):
        """Test city with no available monitoring station."""
        with patch.dict("os.environ", {"OPENAQ_API_KEY": "test-key"}):
            with patch("data_engineering.openaq_client.httpx.AsyncClient.get") as mock_get:
                mock_response = MagicMock()
                mock_response.status_code = 200
                mock_response.json.return_value = SAMPLE_EMPTY_LOCATION_RESPONSE
                mock_get.return_value = mock_response
                
                observations = await fetch_city_air_quality("kuala-lumpur")
                
                assert len(observations) == 0


class TestAirQualityPipeline:
    """Test air quality database pipeline."""

    @pytest.mark.asyncio
    async def test_upsert_air_quality_observation_new(self):
        """Test inserting new air quality observation."""
        mock_session = AsyncMock()
        
        # Mock indicator lookup
        mock_indicator = MagicMock()
        mock_indicator.id = "indicator-uuid-pm25"
        
        # Mock city lookup
        mock_city = MagicMock()
        mock_city.id = "city-uuid-kl"
        
        # Mock execute to return proper async results
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None  # No existing observation
        
        # Set up side_effect for the three execute calls
        async def mock_execute(query):
            if "EnvironmentalIndicator" in str(query):
                return mock_result
            elif "City" in str(query):
                return mock_result
            elif "Observation" in str(query):
                return mock_result
            return mock_result
        
        mock_session.execute.side_effect = mock_execute
        mock_result.scalar_one_or_none.side_effect = [
            mock_indicator,  # First call for indicator
            mock_city,       # Second call for city
            None,            # Third call - no existing observation
        ]
        
        obs = AirQualityObservation(
            city_id="kuala-lumpur",
            indicator_code="pm25",
            observed_at=datetime(2026, 11, 13, 10, 0, 0, tzinfo=timezone.utc),
            value=15.5,
            raw_payload={"source": "openaq", "parameter": "pm25"},
        )
        
        inserted = await upsert_observation(mock_session, obs)
        
        assert inserted is True
        mock_session.add.assert_called_once()
        added_obs = mock_session.add.call_args[0][0]
        assert isinstance(added_obs, Observation)
        assert added_obs.source_type == "external_api"
        assert added_obs.source_name == "openaq"
        assert added_obs.status == "active"

    @pytest.mark.asyncio
    async def test_upsert_air_quality_observation_duplicate(self):
        """Test duplicate air quality observation handling."""
        mock_session = AsyncMock()
        
        mock_indicator = MagicMock()
        mock_indicator.id = "indicator-uuid-pm25"
        mock_city = MagicMock()
        mock_city.id = "city-uuid-kl"
        existing_obs = MagicMock()
        
        # Mock execute to return proper async results
        mock_result = MagicMock()
        
        async def mock_execute(query):
            return mock_result
        
        mock_session.execute.side_effect = mock_execute
        mock_result.scalar_one_or_none.side_effect = [
            mock_indicator,
            mock_city,
            existing_obs,  # Existing observation found
        ]
        
        obs = AirQualityObservation(
            city_id="kuala-lumpur",
            indicator_code="pm25",
            observed_at=datetime(2026, 11, 13, 10, 0, 0, tzinfo=timezone.utc),
            value=15.5,
            raw_payload={},
        )
        
        inserted = await upsert_observation(mock_session, obs)
        
        assert inserted is False
        mock_session.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_ingest_city_air_quality_no_station(self):
        """Test ingestion when no station available."""
        mock_session = AsyncMock()
        
        with patch("data_engineering.pipeline.fetch_city_air_quality") as mock_fetch:
            mock_fetch.return_value = []  # No observations
            
            result = await ingest_city_air_quality(mock_session, "kuala-lumpur")
            
            assert result.successful == 0
            assert result.failed == 0
            assert "No OpenAQ monitoring station available" in result.errors

    @pytest.mark.asyncio
    async def test_ingest_city_air_quality_success(self):
        """Test successful air quality ingestion."""
        mock_session = AsyncMock()
        
        mock_obs = AirQualityObservation(
            city_id="kuala-lumpur",
            indicator_code="pm25",
            observed_at=datetime(2026, 11, 13, 10, 0, 0, tzinfo=timezone.utc),
            value=15.5,
            raw_payload={},
        )
        
        with patch("data_engineering.pipeline.fetch_city_air_quality") as mock_fetch:
            with patch("data_engineering.pipeline.upsert_observation") as mock_upsert:
                mock_fetch.return_value = [mock_obs]
                mock_upsert.return_value = True
                
                result = await ingest_city_air_quality(mock_session, "kuala-lumpur")
                
                assert result.successful == 1
                assert result.failed == 0
                assert result.skipped == 0

    @pytest.mark.asyncio
    async def test_ingest_city_air_quality_http_error(self):
        """Test ingestion handles API errors."""
        mock_session = AsyncMock()
        
        with patch("data_engineering.pipeline.fetch_city_air_quality") as mock_fetch:
            mock_fetch.side_effect = OpenAQHTTPError(500, "Internal Server Error")
            
            result = await ingest_city_air_quality(mock_session, "kuala-lumpur")
            
            assert result.successful == 0
            assert result.failed == 1
            assert "OpenAQ HTTP 500" in result.errors[0]


class TestIndicatorMapping:
    """Test OpenAQ to indicator code mapping."""

    def test_openaq_to_indicator_mapping(self):
        """Verify all expected mappings exist."""
        assert OPENAQ_TO_INDICATOR["pm25"] == "pm25"
        assert OPENAQ_TO_INDICATOR["pm10"] == "pm10"

    def test_supported_parameters_match_seeds(self):
        """Verify mapped parameters exist in seed_indicators.sql."""
        expected_codes = {"pm25", "pm10"}
        mapped_codes = set(OPENAQ_TO_INDICATOR.values())
        assert mapped_codes.issubset(expected_codes)