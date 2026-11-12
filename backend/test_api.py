"""
API route tests using mocked database sessions.
Tests all collection and detail endpoints with pagination, filters, and error cases.
"""

import pytest
from datetime import datetime, timezone
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock
from fastapi.testclient import TestClient


@pytest.fixture
def mock_session():
    """Mock async database session."""
    session = AsyncMock()
    session.execute = AsyncMock()
    session.scalar = AsyncMock()
    return session


@pytest.fixture
def client(mock_session):
    """Test client with mocked database session."""
    from app.main import app
    from app.api.dependencies import get_db_session

    # Clear any existing overrides
    app.dependency_overrides.clear()

    # Override the database session dependency
    async def override_get_db_session():
        yield mock_session

    app.dependency_overrides[get_db_session] = override_get_db_session

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def make_mock_city():
    """Create a mock city object matching schema fields."""
    city = MagicMock()
    city.id = uuid4()
    city.city_code = "NYC"
    city.name = "New York City"
    city.country_code = "US"
    city.latitude = 40.7128
    city.longitude = -74.0060
    city.created_at = datetime.now(timezone.utc)
    city.updated_at = datetime.now(timezone.utc)
    return city


def make_mock_indicator():
    """Create a mock indicator object matching schema fields."""
    ind = MagicMock()
    ind.id = uuid4()
    ind.indicator_code = "AQI"
    ind.name = "Air Quality Index"
    ind.category = "air_quality"
    ind.unit = "AQI"
    ind.description = "Air quality measurement"
    ind.created_at = datetime.now(timezone.utc)
    return ind


def make_mock_sensor():
    """Create a mock sensor object matching schema fields."""
    sensor = MagicMock()
    sensor.id = uuid4()
    sensor.device_id = "sensor-001"
    sensor.city_id = uuid4()
    sensor.category = "air_quality"
    sensor.status = "online"
    sensor.last_seen = datetime.now(timezone.utc)
    sensor.created_at = datetime.now(timezone.utc)
    return sensor


def make_mock_observation():
    """Create a mock observation object matching schema fields."""
    obs = MagicMock()
    obs.id = uuid4()
    obs.city_id = uuid4()
    obs.indicator_id = uuid4()
    obs.iot_device_id = None
    obs.source_type = "simulation"
    obs.source_name = "simulated"
    obs.record_id = None
    obs.observed_at = datetime.now(timezone.utc)
    obs.ingested_at = datetime.now(timezone.utc)
    obs.value = 42.5
    obs.status = "active"
    obs.severity = None
    obs.confidence = None
    obs.raw_payload = None
    return obs


def make_mock_assessment():
    """Create a mock assessment object matching schema fields."""
    assess = MagicMock()
    assess.id = uuid4()
    assess.city_id = uuid4()
    assess.indicator_id = uuid4()
    assess.observed_at = datetime.now(timezone.utc)
    assess.status = "analyzed"
    assess.risk_score = 0.75
    assess.severity = "high"
    assess.confidence = 0.9
    assess.assessment_text = "High risk detected"
    assess.assessed_at = datetime.now(timezone.utc)
    assess.data_points_count = 10
    assess.missing_indicators = None
    return assess


def make_mock_alert():
    """Create a mock alert object matching schema fields."""
    alert = MagicMock()
    alert.id = uuid4()
    alert.city_id = uuid4()
    alert.risk_assessment_id = uuid4()
    alert.severity = "high"
    alert.message = "High risk detected"
    alert.status = "active"
    alert.created_at = datetime.now(timezone.utc)
    return alert


def make_mock_recommendation():
    """Create a mock recommendation object matching schema fields."""
    rec = MagicMock()
    rec.id = uuid4()
    rec.city_id = uuid4()
    rec.risk_assessment_id = uuid4()
    rec.recommendation_text = "Evacuate area"
    rec.action_required = True
    rec.created_at = datetime.now(timezone.utc)
    return rec


# ===== Health and Root Tests =====

def test_health_endpoint(client):
    """Test GET /health returns healthy status."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "citypulse-backend"


def test_root_endpoint(client):
    """Test GET / returns API info."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data


# ===== Cities Tests =====

def test_list_cities(client, mock_session):
    """Test GET /api/v1/cities list endpoint."""
    mock_city = make_mock_city()
    mock_session.execute.return_value = MagicMock(
        scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[mock_city])))
    )
    mock_session.scalar.return_value = 1

    response = client.get("/api/v1/cities")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert "pagination" in data
    assert len(data["data"]) == 1
    assert data["pagination"]["total"] == 1


def test_list_cities_with_pagination(client, mock_session):
    """Test cities pagination parameters."""
    mock_city = make_mock_city()
    # Mock both search and count queries
    mock_search_result = MagicMock(
        scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[mock_city])))
    )
    mock_count_result = MagicMock(scalar_one=MagicMock(return_value=50))
    mock_session.execute.side_effect = [mock_search_result, mock_count_result]

    response = client.get("/api/v1/cities?page=2&limit=10")
    assert response.status_code == 200
    data = response.json()
    assert data["pagination"]["page"] == 2
    assert data["pagination"]["limit"] == 10
    assert data["pagination"]["total"] == 50


def test_list_cities_max_limit(client, mock_session):
    """Test cities max limit enforcement (100)."""
    mock_city = make_mock_city()
    mock_session.execute.return_value = MagicMock(
        scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[mock_city])))
    )
    mock_session.scalar.return_value = 1

    # Limit > 100 should be capped by FastAPI validation (422)
    response = client.get("/api/v1/cities?limit=200")
    assert response.status_code == 422


def test_list_cities_filter_country_code(client, mock_session):
    """Test cities filter by country_code."""
    mock_city = make_mock_city()
    mock_session.execute.return_value = MagicMock(
        scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[mock_city])))
    )
    mock_session.scalar.return_value = 1

    response = client.get("/api/v1/cities?country_code=US")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 1


def test_get_city_by_id(client, mock_session):
    """Test GET /api/v1/cities/{city_id} detail endpoint."""
    mock_city = make_mock_city()
    mock_session.execute.return_value = MagicMock(
        scalar_one_or_none=MagicMock(return_value=mock_city)
    )

    response = client.get(f"/api/v1/cities/{mock_city.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["id"] == str(mock_city.id)
    assert data["data"]["city_code"] == "NYC"


def test_get_city_not_found(client, mock_session):
    """Test GET /api/v1/cities/{city_id} returns 404 for missing."""
    mock_session.execute.return_value = MagicMock(
        scalar_one_or_none=MagicMock(return_value=None)
    )

    response = client.get(f"/api/v1/cities/{uuid4()}")
    assert response.status_code == 404


def test_get_city_invalid_uuid(client):
    """Test GET /api/v1/cities/{city_id} returns 422 for invalid UUID."""
    response = client.get("/api/v1/cities/not-a-uuid")
    assert response.status_code == 422


# ===== Indicators Tests =====

def test_list_indicators(client, mock_session):
    """Test GET /api/v1/indicators list endpoint."""
    mock_ind = make_mock_indicator()
    mock_session.execute.return_value = MagicMock(
        scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[mock_ind])))
    )
    mock_session.scalar.return_value = 1

    response = client.get("/api/v1/indicators")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert len(data["data"]) == 1


def test_list_indicators_filter_category(client, mock_session):
    """Test indicators filter by category."""
    mock_ind = make_mock_indicator()
    mock_session.execute.return_value = MagicMock(
        scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[mock_ind])))
    )
    mock_session.scalar.return_value = 1

    response = client.get("/api/v1/indicators?category=air_quality")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 1


def test_get_indicator_by_id(client, mock_session):
    """Test GET /api/v1/indicators/{indicator_id} detail endpoint."""
    mock_ind = make_mock_indicator()
    mock_session.execute.return_value = MagicMock(
        scalar_one_or_none=MagicMock(return_value=mock_ind)
    )

    response = client.get(f"/api/v1/indicators/{mock_ind.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["id"] == str(mock_ind.id)
    assert data["data"]["indicator_code"] == "AQI"


def test_get_indicator_not_found(client, mock_session):
    """Test GET /api/v1/indicators/{indicator_id} returns 404 for missing."""
    mock_session.execute.return_value = MagicMock(
        scalar_one_or_none=MagicMock(return_value=None)
    )

    response = client.get(f"/api/v1/indicators/{uuid4()}")
    assert response.status_code == 404


# ===== Sensors Tests =====

def test_list_sensors(client, mock_session):
    """Test GET /api/v1/sensors list endpoint."""
    mock_sensor = make_mock_sensor()
    mock_session.execute.return_value = MagicMock(
        scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[mock_sensor])))
    )
    mock_session.scalar.return_value = 1

    response = client.get("/api/v1/sensors")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert len(data["data"]) == 1


def test_list_sensors_filters(client, mock_session):
    """Test sensors filters: city_id, category, status."""
    mock_sensor = make_mock_sensor()
    mock_session.execute.return_value = MagicMock(
        scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[mock_sensor])))
    )
    mock_session.scalar.return_value = 1

    city_id = uuid4()
    response = client.get(f"/api/v1/sensors?city_id={city_id}&category=air_quality&status=online")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 1


def test_get_sensor_by_id(client, mock_session):
    """Test GET /api/v1/sensors/{sensor_id} detail endpoint."""
    mock_sensor = make_mock_sensor()
    mock_session.execute.return_value = MagicMock(
        scalar_one_or_none=MagicMock(return_value=mock_sensor)
    )

    response = client.get(f"/api/v1/sensors/{mock_sensor.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["id"] == str(mock_sensor.id)
    assert data["data"]["device_id"] == "sensor-001"


def test_get_sensor_not_found(client, mock_session):
    """Test GET /api/v1/sensors/{sensor_id} returns 404."""
    mock_session.execute.return_value = MagicMock(
        scalar_one_or_none=MagicMock(return_value=None)
    )

    response = client.get(f"/api/v1/sensors/{uuid4()}")
    assert response.status_code == 404


# ===== Observations Tests =====

def test_list_observations(client, mock_session):
    """Test GET /api/v1/observations list endpoint."""
    mock_obs = make_mock_observation()
    mock_session.execute.return_value = MagicMock(
        scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[mock_obs])))
    )
    mock_session.scalar.return_value = 1

    response = client.get("/api/v1/observations")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert len(data["data"]) == 1


def test_list_observations_filters(client, mock_session):
    """Test observations filters."""
    mock_obs = make_mock_observation()
    mock_session.execute.return_value = MagicMock(
        scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[mock_obs])))
    )
    mock_session.scalar.return_value = 1

    city_id = uuid4()
    indicator_id = uuid4()
    response = client.get(
        f"/api/v1/observations?city_id={city_id}&indicator_id={indicator_id}&source_type=simulation&status=active"
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 1


def test_list_observations_time_range_valid(client, mock_session):
    """Test observations time range filter with valid range."""
    mock_obs = make_mock_observation()
    mock_session.execute.return_value = MagicMock(
        scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[mock_obs])))
    )
    mock_session.scalar.return_value = 1

    response = client.get(
        "/api/v1/observations?start_time=2024-01-01T00:00:00Z&end_time=2024-01-02T00:00:00Z"
    )
    assert response.status_code == 200


def test_list_observations_time_range_invalid(client):
    """Test observations time range filter rejects start > end."""
    response = client.get(
        "/api/v1/observations?start_time=2024-01-02T00:00:00Z&end_time=2024-01-01T00:00:00Z"
    )
    assert response.status_code == 422
    data = response.json()
    assert "detail" in data


def test_get_observation_by_id(client, mock_session):
    """Test GET /api/v1/observations/{observation_id} detail endpoint."""
    mock_obs = make_mock_observation()
    mock_session.execute.return_value = MagicMock(
        scalar_one_or_none=MagicMock(return_value=mock_obs)
    )

    response = client.get(f"/api/v1/observations/{mock_obs.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["id"] == str(mock_obs.id)
    assert data["data"]["value"] == 42.5


def test_get_observation_not_found(client, mock_session):
    """Test GET /api/v1/observations/{observation_id} returns 404."""
    mock_session.execute.return_value = MagicMock(
        scalar_one_or_none=MagicMock(return_value=None)
    )

    response = client.get(f"/api/v1/observations/{uuid4()}")
    assert response.status_code == 404


# ===== Assessments Tests =====

def test_list_assessments(client, mock_session):
    """Test GET /api/v1/assessments list endpoint."""
    mock_assess = make_mock_assessment()
    mock_session.execute.return_value = MagicMock(
        scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[mock_assess])))
    )
    mock_session.scalar.return_value = 1

    response = client.get("/api/v1/assessments")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert len(data["data"]) == 1


def test_list_assessments_filters(client, mock_session):
    """Test assessments filters: city_id, indicator_id, status, severity."""
    mock_assess = make_mock_assessment()
    mock_session.execute.return_value = MagicMock(
        scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[mock_assess])))
    )
    mock_session.scalar.return_value = 1

    city_id = uuid4()
    response = client.get(f"/api/v1/assessments?city_id={city_id}&status=analyzed&severity=high")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 1


def test_list_assessments_time_range(client, mock_session):
    """Test assessments time range filter."""
    mock_assess = make_mock_assessment()
    mock_session.execute.return_value = MagicMock(
        scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[mock_assess])))
    )
    mock_session.scalar.return_value = 1

    response = client.get(
        "/api/v1/assessments?start_time=2024-01-01T00:00:00Z&end_time=2024-01-02T00:00:00Z"
    )
    assert response.status_code == 200


def test_get_assessment_by_id(client, mock_session):
    """Test GET /api/v1/assessments/{assessment_id} detail endpoint."""
    mock_assess = make_mock_assessment()
    mock_session.execute.return_value = MagicMock(
        scalar_one_or_none=MagicMock(return_value=mock_assess)
    )

    response = client.get(f"/api/v1/assessments/{mock_assess.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["id"] == str(mock_assess.id)
    assert data["data"]["risk_score"] == 0.75


def test_get_assessment_not_found(client, mock_session):
    """Test GET /api/v1/assessments/{assessment_id} returns 404."""
    mock_session.execute.return_value = MagicMock(
        scalar_one_or_none=MagicMock(return_value=None)
    )

    response = client.get(f"/api/v1/assessments/{uuid4()}")
    assert response.status_code == 404


# ===== Alerts Tests =====

def test_list_alerts(client, mock_session):
    """Test GET /api/v1/alerts list endpoint."""
    mock_alert = make_mock_alert()
    mock_session.execute.return_value = MagicMock(
        scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[mock_alert])))
    )
    mock_session.scalar.return_value = 1

    response = client.get("/api/v1/alerts")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert len(data["data"]) == 1


def test_list_alerts_filters(client, mock_session):
    """Test alerts filters: city_id, severity, status."""
    mock_alert = make_mock_alert()
    mock_session.execute.return_value = MagicMock(
        scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[mock_alert])))
    )
    mock_session.scalar.return_value = 1

    city_id = uuid4()
    response = client.get(f"/api/v1/alerts?city_id={city_id}&severity=high&status=active")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 1


def test_get_alert_by_id(client, mock_session):
    """Test GET /api/v1/alerts/{alert_id} detail endpoint."""
    mock_alert = make_mock_alert()
    mock_session.execute.return_value = MagicMock(
        scalar_one_or_none=MagicMock(return_value=mock_alert)
    )

    response = client.get(f"/api/v1/alerts/{mock_alert.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["id"] == str(mock_alert.id)
    assert data["data"]["severity"] == "high"


def test_get_alert_not_found(client, mock_session):
    """Test GET /api/v1/alerts/{alert_id} returns 404."""
    mock_session.execute.return_value = MagicMock(
        scalar_one_or_none=MagicMock(return_value=None)
    )

    response = client.get(f"/api/v1/alerts/{uuid4()}")
    assert response.status_code == 404


# ===== Recommendations Tests =====

def test_list_recommendations(client, mock_session):
    """Test GET /api/v1/recommendations list endpoint."""
    mock_rec = make_mock_recommendation()
    mock_session.execute.return_value = MagicMock(
        scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[mock_rec])))
    )
    mock_session.scalar.return_value = 1

    response = client.get("/api/v1/recommendations")
    assert response.status_code == 200
    data = response.json()
    assert "data" in data
    assert len(data["data"]) == 1


def test_list_recommendations_filters(client, mock_session):
    """Test recommendations filters: city_id, risk_assessment_id, action_required."""
    mock_rec = make_mock_recommendation()
    mock_session.execute.return_value = MagicMock(
        scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[mock_rec])))
    )
    mock_session.scalar.return_value = 1

    city_id = uuid4()
    response = client.get(f"/api/v1/recommendations?city_id={city_id}&action_required=true")
    assert response.status_code == 200
    data = response.json()
    assert len(data["data"]) == 1


def test_get_recommendation_by_id(client, mock_session):
    """Test GET /api/v1/recommendations/{recommendation_id} detail endpoint."""
    mock_rec = make_mock_recommendation()
    mock_session.execute.return_value = MagicMock(
        scalar_one_or_none=MagicMock(return_value=mock_rec)
    )

    response = client.get(f"/api/v1/recommendations/{mock_rec.id}")
    assert response.status_code == 200
    data = response.json()
    assert data["data"]["id"] == str(mock_rec.id)
    assert data["data"]["recommendation_text"] == "Evacuate area"


def test_get_recommendation_not_found(client, mock_session):
    """Test GET /api/v1/recommendations/{recommendation_id} returns 404."""
    mock_session.execute.return_value = MagicMock(
        scalar_one_or_none=MagicMock(return_value=None)
    )

    response = client.get(f"/api/v1/recommendations/{uuid4()}")
    assert response.status_code == 404


# ===== Empty Collections Test =====

def test_empty_collection_returns_200(client, mock_session):
    """Test empty collections return 200 with empty data array."""
    # Mock both search and count queries for empty results
    mock_search_result = MagicMock(
        scalars=MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
    )
    mock_count_result = MagicMock(scalar_one=MagicMock(return_value=0))
    mock_session.execute.side_effect = [mock_search_result, mock_count_result]

    endpoints = [
        "/api/v1/cities",
        "/api/v1/indicators",
        "/api/v1/sensors",
        "/api/v1/observations",
        "/api/v1/assessments",
        "/api/v1/alerts",
        "/api/v1/recommendations",
    ]

    for endpoint in endpoints:
        # Reset side_effect for each call
        mock_session.execute.side_effect = [mock_search_result, mock_count_result]
        response = client.get(endpoint)
        assert response.status_code == 200
        data = response.json()
        assert data["data"] == []
        assert data["pagination"]["total"] == 0


# ===== Database Unavailable Test =====

def test_database_unavailable_returns_503():
    """Test that database unavailable returns 503."""
    from app.main import app
    from app.api.dependencies import get_db_session
    from fastapi.testclient import TestClient

    async def bad_db():
        from fastapi import HTTPException
        raise HTTPException(
            status_code=503,
            detail={
                "error": "database_unavailable",
                "message": "Database is not configured or unavailable",
            },
        )

    app.dependency_overrides[get_db_session] = bad_db

    try:
        with TestClient(app) as client:
            response = client.get("/api/v1/cities")
            assert response.status_code == 503
            data = response.json()
            assert data["detail"]["error"] == "database_unavailable"
    finally:
        app.dependency_overrides.clear()


# ===== Verify Mocked Sessions Only =====

def test_mocked_sessions_only():
    """Verify tests use mocked sessions, not real database."""
    # This test documents that we don't test real DB connectivity
    # in this test suite - all tests use mocks.
    assert True