"""
Tests for CityPulse AI Anomaly Detection Engine
"""

import pytest
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from ai_engine.anomaly_engine import AnomalyDetectionEngine


@pytest.fixture
def mock_session():
    """Mock async database session."""
    return AsyncMock()


@pytest.fixture
def mock_city():
    """Mock city object."""
    city = MagicMock()
    city.id = uuid4()
    city.city_code = "kuala-lumpur"
    return city


@pytest.fixture
def mock_indicator():
    """Mock indicator object."""
    ind = MagicMock()
    ind.id = uuid4()
    ind.indicator_code = "temperature"
    ind.unit = "°C"
    return ind


@pytest.fixture
def mock_observation(mock_city, mock_indicator):
    """Mock observation with valid value."""
    obs = MagicMock()
    obs.id = uuid4()
    obs.city_id = mock_city.id
    obs.indicator_id = mock_indicator.id
    obs.value = 35.0
    obs.observed_at = datetime.now(timezone.utc)
    obs.status = "active"
    return obs


@pytest.fixture
def engine(mock_session):
    """AnomalyDetectionEngine instance with mocked dependencies."""
    eng = AnomalyDetectionEngine(mock_session, min_samples=3, z_threshold=2.0)
    eng.city_repo = MagicMock()
    eng.indicator_repo = MagicMock()
    eng.observation_repo = MagicMock()
    return eng


@pytest.mark.asyncio
async def test_insufficient_historical_data(engine, mock_observation):
    """Test insufficient historical data returns insufficient_data status."""
    # Mock historical observations - only 2 samples (< min_samples=3)
    hist_obs1 = MagicMock()
    hist_obs1.id = uuid4()
    hist_obs1.value = 25.0
    hist_obs2 = MagicMock()
    hist_obs2.id = uuid4()
    hist_obs2.value = 26.0

    engine.observation_repo.search = AsyncMock(return_value=[hist_obs1, hist_obs2])

    result = await engine.evaluate_observation(mock_observation)

    assert result["status"] == "insufficient_data"
    assert result["is_anomaly"] is False
    assert result["anomaly_score"] is None
    assert "Insufficient historical data" in result["explanation"]
    assert result["detection_method"] == "rolling_z_score"


@pytest.mark.asyncio
async def test_normal_observation_within_bounds(engine, mock_observation):
    """Test normal observation within 2 standard deviations."""
    # Mock historical observations - sufficient samples
    hist_obs = []
    for i, val in enumerate([24.0, 25.0, 26.0, 25.5, 24.5, 25.2, 24.8]):
        obs = MagicMock()
        obs.id = uuid4()
        obs.value = val
        hist_obs.append(obs)

    engine.observation_repo.search = AsyncMock(return_value=hist_obs)

    # Current observation at 25.0 - well within normal range
    mock_observation.value = 25.0

    result = await engine.evaluate_observation(mock_observation)

    assert result["status"] == "analyzed"
    assert result["is_anomaly"] is False
    assert result["anomaly_score"] is not None
    assert result["anomaly_score"] < 0.5  # Low anomaly score for normal
    assert result["detection_method"] == "rolling_z_score"
    assert "Within normal limits" in result["explanation"]


@pytest.mark.asyncio
async def test_anomaly_observation_outside_bounds(engine, mock_observation):
    """Test observation that is an anomaly (>2 standard deviations)."""
    # Historical: mean ~25, stdev ~1
    hist_obs = []
    for i, val in enumerate([24.0, 25.0, 26.0, 25.5, 24.5, 25.2, 24.8]):
        obs = MagicMock()
        obs.id = uuid4()
        obs.value = val
        hist_obs.append(obs)

    engine.observation_repo.search = AsyncMock(return_value=hist_obs)

    # Current observation at 35.0 - ~10 standard deviations away
    mock_observation.value = 35.0

    result = await engine.evaluate_observation(mock_observation)

    assert result["status"] == "analyzed"
    assert result["is_anomaly"] is True
    assert result["anomaly_score"] is not None
    assert result["anomaly_score"] > 0.5  # High anomaly score
    assert "Anomaly detected" in result["explanation"]


@pytest.mark.asyncio
async def test_missing_observation_value(engine, mock_observation):
    """Test observation with None value."""
    mock_observation.value = None

    hist_obs = []
    for i, val in enumerate([24.0, 25.0, 26.0, 25.5, 24.5, 25.2, 24.8]):
        obs = MagicMock()
        obs.id = uuid4()
        obs.value = val
        hist_obs.append(obs)

    engine.observation_repo.search = AsyncMock(return_value=hist_obs)

    result = await engine.evaluate_observation(mock_observation)

    assert result["status"] == "insufficient_data"
    assert result["is_anomaly"] is False
    assert result["anomaly_score"] is None


@pytest.mark.asyncio
async def test_zero_stdev_historical_data(engine, mock_observation):
    """Test when historical data has zero standard deviation."""
    # All historical values identical
    hist_obs = []
    for i in range(7):
        obs = MagicMock()
        obs.id = uuid4()
        obs.value = 25.0
        hist_obs.append(obs)

    engine.observation_repo.search = AsyncMock(return_value=hist_obs)

    # Current observation different from historical constant
    mock_observation.value = 30.0

    result = await engine.evaluate_observation(mock_observation)

    assert result["status"] == "analyzed"
    assert result["is_anomaly"] is True
    assert result["anomaly_score"] is not None


@pytest.mark.asyncio
async def test_zero_stdev_same_value(engine, mock_observation):
    """Test when historical data has zero stdev and current value matches."""
    hist_obs = []
    for i in range(7):
        obs = MagicMock()
        obs.id = uuid4()
        obs.value = 25.0
        hist_obs.append(obs)

    engine.observation_repo.search = AsyncMock(return_value=hist_obs)

    mock_observation.value = 25.0

    result = await engine.evaluate_observation(mock_observation)

    assert result["status"] == "analyzed"
    assert result["is_anomaly"] is False
    assert result["anomaly_score"] == 0.0


@pytest.mark.asyncio
async def test_detect_anomalies_for_city(engine, mock_city):
    """Test city-level anomaly detection."""
    mock_indicator = MagicMock()
    mock_indicator.id = uuid4()
    mock_indicator.indicator_code = "temperature"

    engine.city_repo.get_by_city_code = AsyncMock(return_value=mock_city)
    engine.indicator_repo.get_all = AsyncMock(return_value=[mock_indicator])

    obs_list = []
    for i, val in enumerate([24.0, 35.0]):
        obs = MagicMock()
        obs.id = uuid4()
        obs.city_id = mock_city.id
        obs.indicator_id = mock_indicator.id
        obs.value = val
        obs.observed_at = datetime.now(timezone.utc)
        obs.status = "active"
        obs_list.append(obs)

    engine.observation_repo.search = AsyncMock(return_value=obs_list)

    # Mock evaluate_observation to return deterministic results
    with patch.object(engine, 'evaluate_observation', new_callable=AsyncMock) as mock_eval:
        mock_eval.side_effect = [
            {"city_id": mock_city.id, "indicator_id": mock_indicator.id, "observed_at": datetime.now(timezone.utc),
             "is_anomaly": False, "anomaly_score": 0.1, "detection_method": "rolling_z_score",
             "explanation": "Normal", "status": "analyzed"},
            {"city_id": mock_city.id, "indicator_id": mock_indicator.id, "observed_at": datetime.now(timezone.utc),
             "is_anomaly": True, "anomaly_score": 0.9, "detection_method": "rolling_z_score",
             "explanation": "Anomaly", "status": "analyzed"},
        ]

        results = await engine.detect_anomalies_for_city("kuala-lumpur")

        assert len(results) == 2
        assert mock_eval.call_count == 2


@pytest.mark.asyncio
async def test_city_not_found(engine):
    """Test city not found raises ValueError."""
    engine.city_repo.get_by_city_code = AsyncMock(return_value=None)

    with pytest.raises(ValueError, match="City not found"):
        await engine.detect_anomalies_for_city("nonexistent")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])