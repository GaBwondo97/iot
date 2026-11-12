"""
Tests for MVP Rule-Based Risk Scoring Engine (Phase 4.4) — Extended Tests.
"""

import pytest
from datetime import datetime, timezone
from decimal import Decimal
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from ai_engine.risk_engine import RiskScoringEngine, THRESHOLDS, run_risk_scoring
from app.db.models import (
    City,
    EnvironmentalIndicator,
    Observation,
    RiskAssessment,
    RiskAssessmentStatus,
    RiskSeverity,
)


class MockObservation:
    def __init__(self, value, observed_at, indicator_id=None):
        self.value = value
        self.observed_at = observed_at
        self.indicator_id = indicator_id or uuid4()


class MockIndicator:
    def __init__(self, code, id=None):
        self.indicator_code = code
        self.id = id or uuid4()


class MockCity:
    def __init__(self, code="kuala-lumpur", id=None):
        self.city_code = code
        self.id = id or uuid4()


class TestRiskScoringEngineLogic:
    """Test pure logic and threshold evaluation of RiskScoringEngine."""

    def test_evaluate_value_temperature(self):
        engine = RiskScoringEngine(None)
        
        # Low risk (< 30.0)
        res = engine._evaluate_value("temperature", 25.0)
        assert res["score"] == 0.1
        assert res["severity"] == "low"

        # Moderate risk (>= 30.0)
        res = engine._evaluate_value("temperature", 32.0)
        assert res["score"] == 0.4
        assert res["severity"] == "moderate"

        # High risk (>= 35.0)
        res = engine._evaluate_value("temperature", 38.0)
        assert res["score"] == 0.7
        assert res["severity"] == "high"

        # Critical risk (>= 40.0)
        res = engine._evaluate_value("temperature", 42.0)
        assert res["score"] == 0.9
        assert res["severity"] == "critical"

    def test_evaluate_value_pm25(self):
        engine = RiskScoringEngine(None)

        # Low (< 12.0)
        res = engine._evaluate_value("pm25", 8.0)
        assert res["score"] == 0.1
        assert res["severity"] == "low"

        # Moderate (>= 12.0)
        res = engine._evaluate_value("pm25", 20.0)
        assert res["score"] == 0.4
        assert res["severity"] == "moderate"

        # High (>= 35.0)
        res = engine._evaluate_value("pm25", 40.0)
        assert res["score"] == 0.7
        assert res["severity"] == "high"

        # Critical (>= 50.0)
        res = engine._evaluate_value("pm25", 60.0)
        assert res["score"] == 0.9
        assert res["severity"] == "critical"

    def test_unknown_indicator(self):
        engine = RiskScoringEngine(None)
        res = engine._evaluate_value("unknown_metric", 100.0)
        assert res["score"] is None
        assert res["severity"] is None
        assert "No threshold rules" in res["explanation"]


class TestRiskScoringEngineDatabase:
    """Test database integration with mocked repositories."""

    @pytest.fixture
    def mock_session(self):
        return AsyncMock()

    @pytest.fixture
    def engine(self, mock_session):
        eng = RiskScoringEngine(mock_session)
        eng.risk_repo.search = AsyncMock(return_value=[])
        return eng

    @pytest.mark.asyncio
    async def test_generate_city_assessments_insufficient_data(self, engine):
        """Test when city has no observations for any indicator."""
        # Mock city lookup
        mock_city = MockCity()
        engine.city_repo.get_by_city_code = AsyncMock(return_value=mock_city)

        # Mock indicator lookup - returns indicators
        mock_indicators = [
            MockIndicator("temperature"),
            MockIndicator("pm25"),
        ]
        engine.indicator_repo.get_by_indicator_code = AsyncMock(
            side_effect=lambda code: next((i for i in mock_indicators if i.indicator_code == code), None)
        )

        # Mock observation search - returns empty (no data)
        engine.observation_repo.search = AsyncMock(return_value=[])

        # Mock risk repo
        engine.risk_repo.get_by_city = AsyncMock(return_value=[])

        # Call
        assessments = await engine.generate_city_assessments("kuala-lumpur")

        # Verify
        assert len(assessments) == 2
        for a in assessments:
            assert a.status == RiskAssessmentStatus.INSUFFICIENT_DATA
            assert a.risk_score is None
            assert a.severity == "Insufficient Data"
            assert a.confidence is None
            assert a.data_points_count == 0
            assert a.missing_indicators is not None

    @pytest.mark.asyncio
    async def test_generate_city_assessments_with_data(self, engine):
        """Test when city has valid observations."""
        mock_city = MockCity()
        engine.city_repo.get_by_city_code = AsyncMock(return_value=mock_city)

        temp_id = uuid4()
        pm25_id = uuid4()
        mock_indicators = [
            MockIndicator("temperature", temp_id),
            MockIndicator("pm25", pm25_id),
        ]
        engine.indicator_repo.get_by_indicator_code = AsyncMock(
            side_effect=lambda code: next((i for i in mock_indicators if i.indicator_code == code), None)
        )

        # Mock observations with values
        temp_obs = MockObservation(38.0, datetime.now(timezone.utc), temp_id)  # high temp
        pm25_obs = MockObservation(40.0, datetime.now(timezone.utc), pm25_id)  # high pm25

        async def mock_search(city_id, indicator_id, status, limit):
            if indicator_id == temp_id:
                return [temp_obs]
            elif indicator_id == pm25_id:
                return [pm25_obs]
            return []

        engine.observation_repo.search = AsyncMock(side_effect=mock_search)

        # Call
        assessments = await engine.generate_city_assessments("kuala-lumpur")

        # Verify
        assert len(assessments) == 2
        
        temp_assessment = next(a for a in assessments if a.indicator_id == temp_id)
        assert temp_assessment.status == RiskAssessmentStatus.ANALYZED
        assert temp_assessment.risk_score == Decimal("0.7")  # high temp
        assert temp_assessment.severity == RiskSeverity.HIGH
        assert temp_assessment.confidence == Decimal("0.80")
        assert temp_assessment.data_points_count == 1

        pm25_assessment = next(a for a in assessments if a.indicator_id == pm25_id)
        assert pm25_assessment.status == RiskAssessmentStatus.ANALYZED
        assert pm25_assessment.risk_score == Decimal("0.7")  # high pm25
        assert pm25_assessment.severity == RiskSeverity.HIGH

    @pytest.mark.asyncio
    async def test_generate_city_assessments_missing_city(self, engine):
        """Test when city doesn't exist."""
        engine.city_repo.get_by_city_code = AsyncMock(return_value=None)
        
        with pytest.raises(ValueError, match="City not found"):
            await engine.generate_city_assessments("nonexistent-city")

    @pytest.mark.asyncio
    async def test_severity_to_score_mapping(self, engine):
        """Test severity to score mapping."""
        assert engine._severity_to_score("low") == 0.1
        assert engine._severity_to_score("moderate") == 0.4
        assert engine._severity_to_score("high") == 0.7
        assert engine._severity_to_score("critical") == 0.9
        assert engine._severity_to_score("unknown") == 0.0

    @pytest.mark.asyncio
    async def test_score_to_severity_mapping(self, engine):
        """Test score to severity mapping."""
        assert engine._score_to_severity(0.9) == "critical"
        assert engine._score_to_severity(0.7) == "critical"  # >= 0.7 is critical
        assert engine._score_to_severity(0.5) == "high"
        assert engine._score_to_severity(0.3) == "moderate"
        assert engine._score_to_severity(0.1) == "low"
        assert engine._score_to_severity(0.0) == "low"


class TestThresholdsCompleteness:
    """Verify all seeded indicators with thresholds have correct units."""

    def test_all_threshold_indicators_have_config(self):
        """All indicators in THRESHOLDS should have unit and three threshold levels."""
        required_keys = {"unit", "critical", "high", "moderate"}
        for indicator_code, config in THRESHOLDS.items():
            assert set(config.keys()) == required_keys, f"{indicator_code} missing keys"
            assert config["critical"] > config["high"] > config["moderate"], f"{indicator_code} thresholds not ordered"

    def test_temperature_unit_celsius(self):
        assert THRESHOLDS["temperature"]["unit"] == "°C"

    def test_pm25_unit_micrograms(self):
        assert THRESHOLDS["pm25"]["unit"] == "µg/m³"

    def test_pm10_unit_micrograms(self):
        assert THRESHOLDS["pm10"]["unit"] == "µg/m³"

    def test_humidity_unit_percent(self):
        assert THRESHOLDS["humidity"]["unit"] == "%"

    def test_rainfall_unit_mm(self):
        assert THRESHOLDS["rainfall"]["unit"] == "mm"

    def test_wind_speed_unit_ms(self):
        assert THRESHOLDS["wind_speed"]["unit"] == "m/s"


class TestDuplicateHandling:
    """Test that duplicate assessment handling works correctly."""

    @pytest.fixture
    def mock_session(self):
        return AsyncMock()

    @pytest.fixture
    def engine(self, mock_session):
        eng = RiskScoringEngine(mock_session)
        eng.risk_repo.search = AsyncMock(return_value=[])
        return eng

    @pytest.mark.asyncio
    async def test_duplicate_observation_does_not_create_duplicate_assessment(self, engine):
        """Running assessment twice should not create duplicates."""
        mock_city = MockCity()
        engine.city_repo.get_by_city_code = AsyncMock(return_value=mock_city)

        temp_id = uuid4()
        mock_indicators = [MockIndicator("temperature", temp_id)]
        engine.indicator_repo.get_by_indicator_code = AsyncMock(
            side_effect=lambda code: next((i for i in mock_indicators if i.indicator_code == code), None)
        )

        temp_obs = MockObservation(38.0, datetime.now(timezone.utc), temp_id)
        engine.observation_repo.search = AsyncMock(return_value=[temp_obs])

        # First run (no existing assessment)
        engine.risk_repo.search = AsyncMock(return_value=[])
        assessments1 = await engine.generate_city_assessments("kuala-lumpur")
        assert len(assessments1) == 1
        assert engine.session.add.call_count == 1

        # Second run - existing assessment returned
        engine.risk_repo.search = AsyncMock(return_value=assessments1)
        assessments2 = await engine.generate_city_assessments("kuala-lumpur")
        assert len(assessments2) == 1
        # No additional add() calls: duplicate was prevented
        assert engine.session.add.call_count == 1
        assert assessments2[0].indicator_id == assessments1[0].indicator_id

        for a in assessments1 + assessments2:
            assert a.status == RiskAssessmentStatus.ANALYZED


class TestIntegrationWithLiveDB:
    """Integration tests requiring live database. Skipped if no DB available."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_live_risk_scoring_execution(self):
        """Test actual risk scoring against Supabase database."""
        from app.db.session import init_db, close_db, AsyncSessionLocal
        
        init_db()
        try:
            async with AsyncSessionLocal() as session:
                results = await run_risk_scoring(session)
        finally:
            await close_db()
            
        # Verify all three cities processed
        assert "kuala-lumpur" in results
        assert "london" in results
        assert "tokyo" in results
        
        # Each city should have 6 assessments (all threshold indicators)
        for city_code, result in results.items():
            assert result["status"] == "success"
            assert result["assessments_count"] == 6
            
            # Check mix of analyzed and insufficient_data
            analyzed = sum(1 for d in result["details"] if d["status"] == "analyzed")
            insufficient = sum(1 for d in result["details"] if d["status"] == "insufficient_data")
            assert analyzed + insufficient == 6
            
            # Temperature should always be analyzed (weather data exists)
            temp_details = [d for d in result["details"] if d["severity"] is not None]
            assert len(temp_details) >= 1  # At least temperature analyzed


class TestRunRiskScoringCLI:
    """Test the CLI entry point."""

    @pytest.fixture
    def mock_session(self):
        return AsyncMock()

    @pytest.fixture
    def engine(self, mock_session):
        eng = RiskScoringEngine(mock_session)
        eng.risk_repo.search = AsyncMock(return_value=[])
        return eng

    @pytest.mark.asyncio
    async def test_run_risk_scoring_returns_dict(self, engine, mock_session):
        """run_risk_scoring should return results for all pilot cities."""
        # Create a mock engine with generate_city_assessments mocked
        mock_engine = MagicMock()
        mock_engine.generate_city_assessments = AsyncMock(
            return_value=[MagicMock(
                indicator_id=uuid4(),
                risk_score=Decimal("0.5"),
                severity=RiskSeverity.MODERATE,
                status=RiskAssessmentStatus.ANALYZED,
            )]
        )
        
        # Patch the RiskScoringEngine constructor to return our mock
        with patch('ai_engine.risk_engine.RiskScoringEngine', return_value=mock_engine):
            results = await run_risk_scoring(mock_session)
        
        assert len(results) == 3  # Three pilot cities
        for city_code in ["kuala-lumpur", "london", "tokyo"]:
            assert city_code in results
            assert results[city_code]["status"] == "success"
            assert results[city_code]["assessments_count"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])