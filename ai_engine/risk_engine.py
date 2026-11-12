"""
CityPulse AI — MVP Rule-Based Risk Scoring Engine

Calculates risk assessments based on heuristic rules using actual database observations.
Thresholds are PRELIMINARY DEMONSTRATION HEURISTICS — NOT scientifically validated.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models import (
    City,
    EnvironmentalIndicator,
    Observation,
    RiskAssessment,
    RiskAssessmentStatus,
    RiskSeverity,
)
from app.repositories.city_repository import CityRepository
from app.repositories.indicator_repository import EnvironmentalIndicatorRepository
from app.repositories.observation_repository import ObservationRepository
from app.repositories.risk_assessment_repository import RiskAssessmentRepository


# PRELIMINARY DEMONSTRATION HEURISTIC THRESHOLDS
# These are NOT scientifically validated values.
# Replace with evidence-based thresholds before production use.
THRESHOLDS = {
    "temperature": {
        "unit": "°C",
        "critical": 40.0,   # Extreme heat
        "high": 35.0,       # Heat warning
        "moderate": 30.0,   # Warm
    },
    "pm25": {
        "unit": "µg/m³",
        "critical": 50.0,   # Unhealthy
        "high": 35.0,       # Unhealthy for sensitive groups
        "moderate": 12.0,   # Moderate
    },
    "pm10": {
        "unit": "µg/m³",
        "critical": 150.0,
        "high": 100.0,
        "moderate": 50.0,
    },
    "humidity": {
        "unit": "%",
        "critical": 95.0,   # Very high (mold risk)
        "high": 85.0,
        "moderate": 70.0,
    },
    "rainfall": {
        "unit": "mm",
        "critical": 50.0,   # Heavy rain / flood risk
        "high": 25.0,
        "moderate": 10.0,
    },
    "wind_speed": {
        "unit": "m/s",
        "critical": 25.0,   # Storm force
        "high": 15.0,
        "moderate": 10.0,
    },
}


class RiskScoringEngine:
    """MVP risk scoring engine using rule-based heuristics."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.city_repo = CityRepository(session)
        self.indicator_repo = EnvironmentalIndicatorRepository(session)
        self.observation_repo = ObservationRepository(session)
        self.risk_repo = RiskAssessmentRepository(session)

    def _evaluate_value(self, indicator_code: str, value: float) -> Dict[str, Any]:
        """
        Evaluate a single observation value against heuristic thresholds.
        Returns score (0.0-1.0), severity, and explanation fragment.
        """
        config = THRESHOLDS.get(indicator_code)
        if not config:
            return {
                "score": None,
                "severity": None,
                "explanation": f"No threshold rules defined for {indicator_code}.",
            }

        if value >= config["critical"]:
            return {
                "score": 0.9,
                "severity": "critical",
                "explanation": (
                    f"{indicator_code}={value}{config['unit']} ≥ "
                    f"{config['critical']}{config['unit']} (critical threshold)"
                ),
            }
        elif value >= config["high"]:
            return {
                "score": 0.7,
                "severity": "high",
                "explanation": (
                    f"{indicator_code}={value}{config['unit']} ≥ "
                    f"{config['high']}{config['unit']} (high threshold)"
                ),
            }
        elif value >= config["moderate"]:
            return {
                "score": 0.4,
                "severity": "moderate",
                "explanation": (
                    f"{indicator_code}={value}{config['unit']} ≥ "
                    f"{config['moderate']}{config['unit']} (moderate threshold)"
                ),
            }
        else:
            return {
                "score": 0.1,
                "severity": "low",
                "explanation": (
                    f"{indicator_code}={value}{config['unit']} below "
                    f"{config['moderate']}{config['unit']} (low risk)"
                ),
            }

    def _severity_to_score(self, severity: str) -> float:
        """Map severity to numeric score for aggregation."""
        mapping = {"low": 0.1, "moderate": 0.4, "high": 0.7, "critical": 0.9}
        return mapping.get(severity, 0.0)

    def _score_to_severity(self, score: float) -> str:
        """Map aggregated score to severity level."""
        if score >= 0.7:
            return "critical"
        elif score >= 0.45:
            return "high"
        elif score >= 0.2:
            return "moderate"
        return "low"

    async def _fetch_latest_observations(
        self, city_id: UUID, indicator_ids: List[UUID]
    ) -> Dict[UUID, Observation]:
        """Fetch the latest valid observation for each indicator in the city."""
        result = {}
        for ind_id in indicator_ids:
            obs = await self.observation_repo.search(
                city_id=city_id,
                indicator_id=ind_id,
                status="active",
                limit=1,
            )
            if obs and obs[0].value is not None:
                result[ind_id] = obs[0]
        return result

    async def generate_city_assessments(
        self, city_code: str
    ) -> List[RiskAssessment]:
        """
        Generate risk assessments for all available indicators in a city.
        Returns list of created RiskAssessment objects.
        """
        # Get city
        city = await self.city_repo.get_by_city_code(city_code)
        if not city:
            raise ValueError(f"City not found: {city_code}")

        # Get all indicators that have threshold rules
        indicator_codes = list(THRESHOLDS.keys())
        indicators = []
        for code in indicator_codes:
            ind = await self.indicator_repo.get_by_indicator_code(code)
            if ind:
                indicators.append(ind)

        if not indicators:
            return []

        indicator_ids = [ind.id for ind in indicators]

        # Fetch latest observations
        observations = await self._fetch_latest_observations(city.id, indicator_ids)

        assessments = []
        new_assessments = []
        for ind in indicators:
            obs = observations.get(ind.id)

            if not obs:
                # Check if latest assessment for this indicator in this city is already INSUFFICIENT_DATA
                existing_inf = await self.risk_repo.search(
                    city_id=city.id,
                    indicator_id=ind.id,
                    status=RiskAssessmentStatus.INSUFFICIENT_DATA.value,
                    limit=1,
                )
                if existing_inf:
                    assessments.append(existing_inf[0])
                    continue

                # Insufficient data for this indicator
                assessment = RiskAssessment(
                    city_id=city.id,
                    indicator_id=ind.id,
                    observed_at=datetime.now(timezone.utc),
                    status=RiskAssessmentStatus.INSUFFICIENT_DATA,
                    risk_score=None,
                    severity="Insufficient Data",
                    confidence=None,
                    assessment_text=(
                        f"No valid observations available for {ind.indicator_code}. "
                        f"Unable to calculate risk score."
                    ),
                    data_points_count=0,
                    missing_indicators=[ind.indicator_code],
                )
                self.session.add(assessment)
                assessments.append(assessment)
                new_assessments.append(assessment)
            else:
                # Check if assessment for this specific observation already exists to prevent duplicate creation
                existing_obs_assessment = await self.risk_repo.search(
                    city_id=city.id,
                    indicator_id=ind.id,
                    limit=1,
                )
                if existing_obs_assessment and existing_obs_assessment[0].observed_at == obs.observed_at:
                    assessments.append(existing_obs_assessment[0])
                    continue

                # Evaluate
                eval_result = self._evaluate_value(ind.indicator_code, float(obs.value))
                if eval_result["score"] is None:
                    assessment = RiskAssessment(
                        city_id=city.id,
                        indicator_id=ind.id,
                        observed_at=obs.observed_at,
                        status=RiskAssessmentStatus.INSUFFICIENT_DATA,
                        risk_score=None,
                        severity="Insufficient Data",
                        confidence=None,
                        assessment_text=(
                            f"No threshold rules defined for {ind.indicator_code}. "
                            f"Unable to calculate risk score."
                        ),
                        data_points_count=1,
                        missing_indicators=[ind.indicator_code],
                    )
                else:
                    assessment = RiskAssessment(
                        city_id=city.id,
                        indicator_id=ind.id,
                        observed_at=obs.observed_at,
                        status=RiskAssessmentStatus.ANALYZED,
                        risk_score=Decimal(str(eval_result["score"])),
                        severity=RiskSeverity(eval_result["severity"]),
                        confidence=Decimal("0.80"),  # Baseline heuristic indicator
                        assessment_text=(
                            f"Risk assessment for {ind.indicator_code}: "
                            f"{eval_result['explanation']}. "
                            f"[Heuristic rule evaluation; confidence is a baseline heuristic indicator, not statistically validated.]"
                        ),
                        data_points_count=1,
                        missing_indicators=None,
                    )

                self.session.add(assessment)
                assessments.append(assessment)
                new_assessments.append(assessment)

        if new_assessments:
            await self.session.commit()
            for a in new_assessments:
                await self.session.refresh(a)

        return assessments

    async def get_assessments_for_city(self, city_code: str) -> List[RiskAssessment]:
        """Retrieve existing assessments for a city."""
        city = await self.city_repo.get_by_city_code(city_code)
        if not city:
            return []
        return await self.risk_repo.get_by_city(city.id)


async def run_risk_scoring(session: AsyncSession) -> Dict[str, Any]:
    """
    CLI entry point: generate risk assessments for all pilot cities.
    """
    engine = RiskScoringEngine(session)
    pilot_cities = ["kuala-lumpur", "london", "tokyo"]

    results = {}
    for city_code in pilot_cities:
        try:
            assessments = await engine.generate_city_assessments(city_code)
            results[city_code] = {
                "status": "success",
                "assessments_count": len(assessments),
                "details": [
                    {
                        "indicator": str(a.indicator_id),
                        "risk_score": str(a.risk_score) if a.risk_score else None,
                        "severity": a.severity.value if a.severity and hasattr(a.severity, 'value') else str(a.severity) if a.severity else None,
                        "status": a.status.value if a.status and hasattr(a.status, 'value') else str(a.status) if a.status else None,
                    }
                    for a in assessments
                ],
            }
        except Exception as e:
            import traceback
            traceback.print_exc()
            results[city_code] = {"status": "error", "error": str(e)}

    return results