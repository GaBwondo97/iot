"""
CityPulse AI — MVP Statistical Anomaly Detection Engine

Detects anomalies in environmental observations using rolling historical baselines (Z-score).
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from decimal import Decimal
from uuid import UUID
import statistics

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.models import (
    City,
    EnvironmentalIndicator,
    Observation,
)
from app.repositories.city_repository import CityRepository
from app.repositories.indicator_repository import EnvironmentalIndicatorRepository
from app.repositories.observation_repository import ObservationRepository


class AnomalyDetectionEngine:
    """MVP anomaly detection engine using rolling historical Z-scores."""

    def __init__(self, session: AsyncSession, min_samples: int = 5, z_threshold: float = 2.0):
        self.session = session
        self.city_repo = CityRepository(session)
        self.indicator_repo = EnvironmentalIndicatorRepository(session)
        self.observation_repo = ObservationRepository(session)
        self.min_samples = min_samples
        self.z_threshold = z_threshold

    async def evaluate_observation(self, observation: Observation) -> Dict[str, Any]:
        """
        Evaluate a single observation against historical observations for the same city and indicator.
        Returns anomaly evaluation dict matching output contract.
        """
        # Fetch historical active observations for this city & indicator
        historical = await self.observation_repo.search(
            city_id=observation.city_id,
            indicator_id=observation.indicator_id,
            status="active",
            limit=100,
        )

        # Filter out the current observation if already stored
        historical = [obs for obs in historical if obs.id != observation.id and obs.value is not None]

        if len(historical) < self.min_samples or observation.value is None:
            return {
                "city_id": observation.city_id,
                "indicator_id": observation.indicator_id,
                "observed_at": observation.observed_at,
                "is_anomaly": False,
                "anomaly_score": None,
                "detection_method": "rolling_z_score",
                "explanation": f"Insufficient historical data ({len(historical)} samples found, min required {self.min_samples}).",
                "status": "insufficient_data",
            }

        values = [float(obs.value) for obs in historical]
        val = float(observation.value)

        mean_val = statistics.mean(values)
        try:
            stdev_val = statistics.stdev(values)
        except statistics.StatisticsError:
            stdev_val = 0.0

        if stdev_val == 0.0:
            # If historical stdev is zero, any difference is an anomaly if value differs, or not if identical
            is_anomaly = val != mean_val
            z_score = 0.0 if not is_anomaly else 9.99
        else:
            z_score = (val - mean_val) / stdev_val
            is_anomaly = abs(z_score) >= self.z_threshold

        # Anomaly score bounded 0.0 to 1.0 based on z_score magnitude
        anomaly_score = min(max(abs(z_score) / (self.z_threshold * 2.0), 0.0), 1.0)

        explanation = (
            f"Value {val} has Z-score {z_score:.2f} "
            f"(historical mean={mean_val:.2f}, stdev={stdev_val:.2f}, threshold={self.z_threshold}). "
            f"{'Anomaly detected.' if is_anomaly else 'Within normal limits.'}"
        )

        return {
            "city_id": observation.city_id,
            "indicator_id": observation.indicator_id,
            "observed_at": observation.observed_at,
            "is_anomaly": is_anomaly,
            "anomaly_score": round(anomaly_score, 2),
            "detection_method": "rolling_z_score",
            "explanation": explanation,
            "status": "analyzed",
        }

    async def detect_anomalies_for_city(self, city_code: str) -> List[Dict[str, Any]]:
        """
        Run anomaly detection across all recent observations for a city.
        """
        city = await self.city_repo.get_by_city_code(city_code)
        if not city:
            raise ValueError(f"City not found: {city_code}")

        indicators = await self.indicator_repo.get_all()
        results = []

        for ind in indicators:
            obs_list = await self.observation_repo.search(
                city_id=city.id,
                indicator_id=ind.id,
                status="active",
                limit=10,
            )
            for obs in obs_list:
                eval_res = await self.evaluate_observation(obs)
                results.append(eval_res)

        return results
