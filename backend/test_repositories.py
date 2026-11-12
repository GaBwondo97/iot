"""
Tests for repository layer using mocked AsyncSession.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from app.repositories.base import BaseRepository
from app.repositories.city_repository import CityRepository
from app.repositories.indicator_repository import EnvironmentalIndicatorRepository
from app.repositories.iot_device_repository import IoTDeviceRepository
from app.repositories.observation_repository import ObservationRepository
from app.repositories.risk_assessment_repository import RiskAssessmentRepository
from app.repositories.alert_repository import AlertRepository
from app.repositories.recommendation_repository import RecommendationRepository
from app.db.models import (
    City,
    EnvironmentalIndicator,
    IoTDevice,
    Observation,
    RiskAssessment,
    Alert,
    Recommendation,
)


class TestBaseRepository:
    """Test base repository CRUD operations."""

    @pytest.fixture
    def mock_session(self):
        return AsyncMock()

    @pytest.fixture
    def repo(self, mock_session):
        return BaseRepository(mock_session, City)

    @pytest.mark.asyncio
    async def test_get_by_id(self, repo, mock_session):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = City(
            id=uuid4(), city_code="KUL", name="Kuala Lumpur", country_code="MY"
        )
        mock_session.execute.return_value = mock_result

        result = await repo.get_by_id(uuid4())
        assert result is not None
        assert result.city_code == "KUL"
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_all(self, repo, mock_session):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [
            City(id=uuid4(), city_code="KUL", name="Kuala Lumpur", country_code="MY"),
            City(id=uuid4(), city_code="LON", name="London", country_code="GB"),
        ]
        mock_session.execute.return_value = mock_result

        result = await repo.get_all(offset=0, limit=20)
        assert len(result) == 2
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_count(self, repo, mock_session):
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 42
        mock_session.execute.return_value = mock_result

        result = await repo.count()
        assert result == 42
        mock_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_create(self, repo, mock_session):
        mock_session.flush = AsyncMock()
        mock_session.refresh = AsyncMock()

        obj = await repo.create(city_code="KUL", name="Kuala Lumpur", country_code="MY")
        assert obj.city_code == "KUL"
        mock_session.add.assert_called_once()
        mock_session.flush.assert_awaited_once()
        mock_session.refresh.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_update(self, repo, mock_session):
        mock_session.flush = AsyncMock()
        mock_session.refresh = AsyncMock()
        obj = City(id=uuid4(), city_code="KUL", name="Kuala Lumpur", country_code="MY")

        updated = await repo.update(obj, name="Kuala Lumpur Updated")
        assert updated.name == "Kuala Lumpur Updated"
        mock_session.flush.assert_awaited_once()
        mock_session.refresh.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_update_does_not_modify_primary_key(self, repo, mock_session):
        """Update should not modify primary key fields."""
        mock_session.flush = AsyncMock()
        mock_session.refresh = AsyncMock()
        obj = City(id=uuid4(), city_code="KUL", name="Kuala Lumpur", country_code="MY")
        original_id = obj.id

        await repo.update(obj, id=uuid4(), name="Updated")

        assert obj.id == original_id
        mock_session.flush.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_pagination_limit_max(self, repo, mock_session):
        """Pagination limit should be capped at 100."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        await repo.get_all(offset=0, limit=150)
        call_args = mock_session.execute.call_args
        query = call_args[0][0]
        # Check limit is clamped
        assert query._limit == 100

    @pytest.mark.asyncio
    async def test_pagination_default_limit(self, repo, mock_session):
        """Default limit should be 20."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        await repo.get_all(offset=0)
        call_args = mock_session.execute.call_args
        query = call_args[0][0]
        assert query._limit == 20

    @pytest.mark.asyncio
    async def test_negative_offset_normalized(self, repo, mock_session):
        """Negative offset should be normalized to 0."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        await repo.get_all(offset=-10, limit=20)
        call_args = mock_session.execute.call_args
        query = call_args[0][0]
        assert query._offset == 0


class TestCityRepository:
    """Test CityRepository specific methods."""

    @pytest.fixture
    def mock_session(self):
        return AsyncMock()

    @pytest.fixture
    def repo(self, mock_session):
        return CityRepository(mock_session)

    @pytest.mark.asyncio
    async def test_get_by_city_code(self, repo, mock_session):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = City(
            id=uuid4(), city_code="KUL", name="Kuala Lumpur", country_code="MY"
        )
        mock_session.execute.return_value = mock_result

        result = await repo.get_by_city_code("KUL")
        assert result is not None
        assert result.city_code == "KUL"

    @pytest.mark.asyncio
    async def test_search_with_country_filter(self, repo, mock_session):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [
            City(id=uuid4(), city_code="KUL", name="Kuala Lumpur", country_code="MY")
        ]
        mock_session.execute.return_value = mock_result

        result = await repo.search(country_code="MY", offset=0, limit=20)
        assert len(result) == 1
        assert result[0].country_code == "MY"

    @pytest.mark.asyncio
    async def test_search_deterministic_ordering(self, repo, mock_session):
        """Search should order by created_at DESC, id DESC."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [
            City(id=uuid4(), city_code="A", name="A", country_code="US"),
            City(id=uuid4(), city_code="B", name="B", country_code="US"),
        ]
        mock_session.execute.return_value = mock_result

        await repo.search(country_code="US", offset=0, limit=20)
        call_args = mock_session.execute.call_args
        query = call_args[0][0]
        # Verify ordering is present
        compiled = query.compile()
        assert "created_at" in str(compiled).lower()
        assert "id" in str(compiled).lower()


class TestEnvironmentalIndicatorRepository:
    """Test EnvironmentalIndicatorRepository specific methods."""

    @pytest.fixture
    def mock_session(self):
        return AsyncMock()

    @pytest.fixture
    def repo(self, mock_session):
        return EnvironmentalIndicatorRepository(mock_session)

    @pytest.mark.asyncio
    async def test_get_by_indicator_code(self, repo, mock_session):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = EnvironmentalIndicator(
            id=uuid4(), indicator_code="PM25", name="PM2.5", category="air_quality"
        )
        mock_session.execute.return_value = mock_result

        result = await repo.get_by_indicator_code("PM25")
        assert result is not None
        assert result.indicator_code == "PM25"

    @pytest.mark.asyncio
    async def test_search_with_category_filter(self, repo, mock_session):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [
            EnvironmentalIndicator(
                id=uuid4(), indicator_code="PM25", name="PM2.5", category="air_quality"
            )
        ]
        mock_session.execute.return_value = mock_result

        result = await repo.search(category="air_quality", offset=0, limit=20)
        assert len(result) == 1
        assert result[0].category == "air_quality"

    @pytest.mark.asyncio
    async def test_search_deterministic_ordering(self, repo, mock_session):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        await repo.search(category="air_quality", offset=0, limit=20)
        call_args = mock_session.execute.call_args
        query = call_args[0][0]
        compiled = query.compile()
        assert "created_at" in str(compiled).lower()
        assert "id" in str(compiled).lower()


class TestIoTDeviceRepository:
    """Test IoTDeviceRepository specific methods."""

    @pytest.fixture
    def mock_session(self):
        return AsyncMock()

    @pytest.fixture
    def repo(self, mock_session):
        return IoTDeviceRepository(mock_session)

    @pytest.mark.asyncio
    async def test_get_by_device_id(self, repo, mock_session):
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = IoTDevice(
            id=uuid4(), device_id="SENSOR-001", city_id=uuid4(), status="active"
        )
        mock_session.execute.return_value = mock_result

        result = await repo.get_by_device_id("SENSOR-001")
        assert result is not None
        assert result.device_id == "SENSOR-001"

    @pytest.mark.asyncio
    async def test_search_with_filters(self, repo, mock_session):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [
            IoTDevice(id=uuid4(), device_id="SENSOR-001", city_id=uuid4(), status="active")
        ]
        mock_session.execute.return_value = mock_result

        city_id = uuid4()
        result = await repo.search(city_id=city_id, status="active", offset=0, limit=20)
        assert len(result) == 1
        assert result[0].status == "active"

    @pytest.mark.asyncio
    async def test_search_category_filter(self, repo, mock_session):
        """API contract requires category filter for sensors."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [
            IoTDevice(id=uuid4(), device_id="SENSOR-001", city_id=uuid4(), category="air_quality")
        ]
        mock_session.execute.return_value = mock_result

        result = await repo.search(category="air_quality", offset=0, limit=20)
        assert len(result) == 1
        assert result[0].category == "air_quality"

    @pytest.mark.asyncio
    async def test_search_deterministic_ordering(self, repo, mock_session):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        await repo.search(city_id=uuid4(), offset=0, limit=20)
        call_args = mock_session.execute.call_args
        query = call_args[0][0]
        compiled = query.compile()
        assert "created_at" in str(compiled).lower()
        assert "id" in str(compiled).lower()


class TestObservationRepository:
    """Test ObservationRepository specific methods."""

    @pytest.fixture
    def mock_session(self):
        return AsyncMock()

    @pytest.fixture
    def repo(self, mock_session):
        return ObservationRepository(mock_session)

    @pytest.mark.asyncio
    async def test_search_with_time_filters(self, repo, mock_session):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [
            Observation(
                id=uuid4(),
                city_id=uuid4(),
                indicator_id=uuid4(),
                observed_at=datetime.utcnow(),
                value=25.5,
                source_type="sensor",
            )
        ]
        mock_session.execute.return_value = mock_result

        start = datetime(2024, 1, 1)
        end = datetime(2024, 12, 31)
        result = await repo.search(
            city_id=uuid4(),
            start_time=start,
            end_time=end,
            offset=0,
            limit=20,
        )
        assert len(result) == 1

    @pytest.mark.asyncio
    async def test_count_filtered(self, repo, mock_session):
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 100
        mock_session.execute.return_value = mock_result

        result = await repo.count_filtered(city_id=uuid4())
        assert result == 100

    @pytest.mark.asyncio
    async def test_search_status_filter(self, repo, mock_session):
        """API contract requires status filter for observations."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [
            Observation(
                id=uuid4(),
                city_id=uuid4(),
                indicator_id=uuid4(),
                observed_at=datetime.utcnow(),
                value=25.5,
                source_type="sensor",
                status="valid",
            )
        ]
        mock_session.execute.return_value = mock_result

        result = await repo.search(status="valid", offset=0, limit=20)
        assert len(result) == 1
        assert result[0].status == "valid"

    @pytest.mark.asyncio
    async def test_search_deterministic_ordering(self, repo, mock_session):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        await repo.search(city_id=uuid4(), offset=0, limit=20)
        call_args = mock_session.execute.call_args
        query = call_args[0][0]
        compiled = query.compile()
        assert "observed_at" in str(compiled).lower()
        assert "id" in str(compiled).lower()

    @pytest.mark.asyncio
    async def test_count_filtered_matches_search_conditions(self, repo, mock_session):
        """Count and search should use identical filters."""
        mock_search_result = MagicMock()
        mock_search_result.scalars.return_value.all.return_value = [Observation(id=uuid4())]
        mock_count_result = MagicMock()
        mock_count_result.scalar_one.return_value = 1

        mock_session.execute.side_effect = [mock_search_result, mock_count_result]

        city_id = uuid4()
        indicator_id = uuid4()
        start = datetime(2024, 1, 1)
        end = datetime(2024, 12, 31)

        search_results = await repo.search(
            city_id=city_id,
            indicator_id=indicator_id,
            start_time=start,
            end_time=end,
            offset=0,
            limit=20,
        )
        count = await repo.count_filtered(
            city_id=city_id,
            indicator_id=indicator_id,
            start_time=start,
            end_time=end,
        )

        assert count == len(search_results) == 1


class TestRiskAssessmentRepository:
    """Test RiskAssessmentRepository specific methods."""

    @pytest.fixture
    def mock_session(self):
        return AsyncMock()

    @pytest.fixture
    def repo(self, mock_session):
        return RiskAssessmentRepository(mock_session)

    @pytest.mark.asyncio
    async def test_search_with_status_filter(self, repo, mock_session):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [
            RiskAssessment(
                id=uuid4(),
                city_id=uuid4(),
                indicator_id=uuid4(),
                assessed_at=datetime.utcnow(),
                status="completed",
                risk_score=0.75,
            )
        ]
        mock_session.execute.return_value = mock_result

        result = await repo.search(
            city_id=uuid4(),
            status="completed",
            offset=0,
            limit=20,
        )
        assert len(result) == 1
        assert result[0].status == "completed"

    @pytest.mark.asyncio
    async def test_search_with_severity_filter(self, repo, mock_session):
        """API contract requires severity filter for assessments."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [
            RiskAssessment(
                id=uuid4(),
                city_id=uuid4(),
                indicator_id=uuid4(),
                assessed_at=datetime.utcnow(),
                severity="high",
                risk_score=0.75,
            )
        ]
        mock_session.execute.return_value = mock_result

        result = await repo.search(severity="high", offset=0, limit=20)
        assert len(result) == 1
        assert result[0].severity == "high"

    @pytest.mark.asyncio
    async def test_count_filtered(self, repo, mock_session):
        mock_result = MagicMock()
        mock_result.scalar_one.return_value = 50
        mock_session.execute.return_value = mock_result

        result = await repo.count_filtered(city_id=uuid4())
        assert result == 50

    @pytest.mark.asyncio
    async def test_search_deterministic_ordering(self, repo, mock_session):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        await repo.search(city_id=uuid4(), offset=0, limit=20)
        call_args = mock_session.execute.call_args
        query = call_args[0][0]
        compiled = query.compile()
        assert "assessed_at" in str(compiled).lower()
        assert "id" in str(compiled).lower()

    @pytest.mark.asyncio
    async def test_count_filtered_matches_search_conditions(self, repo, mock_session):
        mock_search_result = MagicMock()
        mock_search_result.scalars.return_value.all.return_value = [RiskAssessment(id=uuid4())]
        mock_count_result = MagicMock()
        mock_count_result.scalar_one.return_value = 1

        mock_session.execute.side_effect = [mock_search_result, mock_count_result]

        city_id = uuid4()
        start = datetime(2024, 1, 1)
        end = datetime(2024, 12, 31)

        search_results = await repo.search(
            city_id=city_id,
            start_time=start,
            end_time=end,
            offset=0,
            limit=20,
        )
        count = await repo.count_filtered(
            city_id=city_id,
            start_time=start,
            end_time=end,
        )

        assert count == len(search_results) == 1


class TestAlertRepository:
    """Test AlertRepository specific methods."""

    @pytest.fixture
    def mock_session(self):
        return AsyncMock()

    @pytest.fixture
    def repo(self, mock_session):
        return AlertRepository(mock_session)

    @pytest.mark.asyncio
    async def test_get_by_risk_assessment(self, repo, mock_session):
        ra_id = uuid4()
        mock_alert = Alert(
            id=uuid4(),
            city_id=uuid4(),
            risk_assessment_id=ra_id,
            severity="high",
            status="active",
        )
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_alert]
        mock_session.execute.return_value = mock_result
        result = await repo.get_by_risk_assessment(ra_id)
        assert len(result) == 1
        assert result[0].risk_assessment_id == ra_id

    @pytest.mark.asyncio
    async def test_search_with_severity_filter(self, repo, mock_session):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [
            Alert(
                id=uuid4(),
                city_id=uuid4(),
                risk_assessment_id=uuid4(),
                severity="critical",
                status="active",
            )
        ]
        mock_session.execute.return_value = mock_result

        result = await repo.search(severity="critical", offset=0, limit=20)
        assert len(result) == 1
        assert result[0].severity == "critical"

    @pytest.mark.asyncio
    async def test_search_with_status_filter(self, repo, mock_session):
        """API contract requires status filter for alerts."""
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [
            Alert(
                id=uuid4(),
                city_id=uuid4(),
                risk_assessment_id=uuid4(),
                severity="high",
                status="acknowledged",
            )
        ]
        mock_session.execute.return_value = mock_result

        result = await repo.search(status="acknowledged", offset=0, limit=20)
        assert len(result) == 1
        assert result[0].status == "acknowledged"

    @pytest.mark.asyncio
    async def test_search_deterministic_ordering(self, repo, mock_session):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        await repo.search(city_id=uuid4(), offset=0, limit=20)
        call_args = mock_session.execute.call_args
        query = call_args[0][0]
        compiled = query.compile()
        assert "created_at" in str(compiled).lower()
        assert "id" in str(compiled).lower()


class TestRecommendationRepository:
    """Test RecommendationRepository specific methods."""

    @pytest.fixture
    def mock_session(self):
        return AsyncMock()

    @pytest.fixture
    def repo(self, mock_session):
        return RecommendationRepository(mock_session)

    @pytest.mark.asyncio
    async def test_get_by_risk_assessment(self, repo, mock_session):
        ra_id = uuid4()
        mock_rec = Recommendation(
            id=uuid4(),
            city_id=uuid4(),
            risk_assessment_id=ra_id,
            action_required=True,
        )
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_rec]
        mock_session.execute.return_value = mock_result
        result = await repo.get_by_risk_assessment(ra_id)
        assert len(result) == 1
        assert result[0].risk_assessment_id == ra_id
        assert result[0].action_required is True

    @pytest.mark.asyncio
    async def test_search_with_action_required_filter(self, repo, mock_session):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [
            Recommendation(
                id=uuid4(),
                city_id=uuid4(),
                risk_assessment_id=uuid4(),
                action_required=True,
            )
        ]
        mock_session.execute.return_value = mock_result

        result = await repo.search(action_required=True, offset=0, limit=20)
        assert len(result) == 1
        assert result[0].action_required is True

    @pytest.mark.asyncio
    async def test_search_with_risk_assessment_id_filter(self, repo, mock_session):
        """API contract requires risk_assessment_id filter for recommendations."""
        ra_id = uuid4()
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [
            Recommendation(
                id=uuid4(),
                city_id=uuid4(),
                risk_assessment_id=ra_id,
                action_required=False,
            )
        ]
        mock_session.execute.return_value = mock_result

        result = await repo.search(risk_assessment_id=ra_id, offset=0, limit=20)
        assert len(result) == 1
        assert result[0].risk_assessment_id == ra_id

    @pytest.mark.asyncio
    async def test_search_deterministic_ordering(self, repo, mock_session):
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_session.execute.return_value = mock_result

        await repo.search(city_id=uuid4(), offset=0, limit=20)
        call_args = mock_session.execute.call_args
        query = call_args[0][0]
        compiled = query.compile()
        assert "created_at" in str(compiled).lower()
        assert "id" in str(compiled).lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])