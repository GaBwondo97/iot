"""Data Ingestion Pipeline for CityPulse AI.

This module provides:
- External API ingestion (Open-Meteo weather, OpenAQ air quality)
- IoT message processing pipeline (parse, validate, normalize, deduplicate)
"""

import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import List, Optional, Tuple, Union, Dict, Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import City, EnvironmentalIndicator, Observation as DBObservation
from data_engineering.open_meteo_client import (
    WeatherObservation,
    fetch_current_weather,
    OpenMeteoError,
)
from data_engineering.openaq_client import (
    AirQualityObservation,
    fetch_city_air_quality,
    OpenAQError,
)

log = logging.getLogger(__name__)

# Union type for external API observation types
AnyObservation = Union[WeatherObservation, AirQualityObservation]


@dataclass
class IngestionResult:
    """Result of ingesting weather/air quality data for one city."""
    city_code: str
    successful: int = 0
    skipped: int = 0
    failed: int = 0
    errors: Optional[List[str]] = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []


async def get_or_create_city(session: AsyncSession, city_code: str) -> Optional[City]:
    """Get city by city_code."""
    result = await session.execute(
        select(City).where(City.city_code == city_code)
    )
    return result.scalar_one_or_none()


async def get_indicator(session: AsyncSession, indicator_code: str) -> Optional[EnvironmentalIndicator]:
    """Get indicator by indicator_code."""
    result = await session.execute(
        select(EnvironmentalIndicator).where(EnvironmentalIndicator.indicator_code == indicator_code)
    )
    return result.scalar_one_or_none()


async def upsert_observation(
    session: AsyncSession,
    obs: AnyObservation,
) -> bool:
    """
    Insert observation, handling duplicates via unique constraint.

    Returns:
        True if inserted, False if duplicate (skipped)
    """
    # Get city and indicator UUIDs
    city = await get_or_create_city(session, obs.city_id)
    if not city:
        raise ValueError(f"City not found: {obs.city_id}")

    indicator = await get_indicator(session, obs.indicator_code)
    if not indicator:
        raise ValueError(f"Indicator not found: {obs.indicator_code}")

    # Determine source_name based on observation type
    source_name = "open_meteo" if isinstance(obs, WeatherObservation) else "openaq"

    # Check for existing observation (deduplication)
    existing = await session.execute(
        select(DBObservation).where(
            DBObservation.city_id == city.id,
            DBObservation.indicator_id == indicator.id,
            DBObservation.observed_at == obs.observed_at,
            DBObservation.source_type == "external_api",
        )
    )
    if existing.scalar_one_or_none():
        return False  # Duplicate, skipped

    # Create new observation
    new_obs = DBObservation(
        city_id=city.id,
        indicator_id=indicator.id,
        iot_device_id=None,
        source_type="external_api",
        source_name=source_name,
        record_id=None,
        observed_at=obs.observed_at,
        ingested_at=datetime.now(timezone.utc),
        value=obs.value,
        status="active",
        severity=None,
        confidence=None,
        raw_payload=obs.raw_payload,
    )
    session.add(new_obs)
    return True


async def ingest_city_weather(
    session: AsyncSession,
    city_code: str,
) -> IngestionResult:
    """
    Fetch and ingest weather for a single city.
    """
    result = IngestionResult(city_code=city_code)

    try:
        observations = await fetch_current_weather(city_code)
    except OpenMeteoError as e:
        result.failed = 1
        result.errors.append(str(e))
        return result

    for obs in observations:
        try:
            inserted = await upsert_observation(session, obs)
            if inserted:
                result.successful += 1
            else:
                result.skipped += 1
        except Exception as e:
            result.failed += 1
            result.errors.append(f"{obs.indicator_code}: {e}")

    return result


async def run_weather_ingestion() -> List[IngestionResult]:
    """
    Run weather ingestion for all pilot cities.

    Returns list of IngestionResult per city.
    """
    from app.db.session import AsyncSessionLocal

    results = []

    async with AsyncSessionLocal() as session:
        # Import here to avoid circular imports
        from data_engineering.config import get_all_city_codes

        for city_code in get_all_city_codes():
            log.info(f"Processing city: {city_code}")
            city_result = await ingest_city_weather(session, city_code)
            results.append(city_result)

            # Commit after each city to avoid long transactions
            try:
                await session.commit()
            except Exception as e:
                await session.rollback()
                city_result.failed += city_result.successful
                city_result.successful = 0
                city_result.errors.append(f"Commit failed: {e}")

    return results


async def ingest_city_air_quality(
    session: AsyncSession,
    city_code: str,
) -> IngestionResult:
    """
    Fetch and ingest air quality for a single city.
    """
    result = IngestionResult(city_code=city_code)

    try:
        observations = await fetch_city_air_quality(city_code)
    except OpenAQError as e:
        result.failed = 1
        result.errors.append(str(e))
        return result

    if not observations:
        result.errors.append("No OpenAQ monitoring station available")
        return result

    for obs in observations:
        try:
            inserted = await upsert_observation(session, obs)
            if inserted:
                result.successful += 1
            else:
                result.skipped += 1
        except Exception as e:
            result.failed += 1
            result.errors.append(f"{obs.indicator_code}: {e}")

    return result


async def run_air_quality_ingestion() -> List[IngestionResult]:
    """
    Run air quality ingestion for all pilot cities.

    Returns list of IngestionResult per city.
    """
    from app.db.session import AsyncSessionLocal

    results = []

    async with AsyncSessionLocal() as session:
        from data_engineering.config import get_all_city_codes

        for city_code in get_all_city_codes():
            log.info(f"Processing air quality for city: {city_code}")
            city_result = await ingest_city_air_quality(session, city_code)
            results.append(city_result)

            try:
                await session.commit()
            except Exception as e:
                await session.rollback()
                city_result.failed += city_result.successful
                city_result.successful = 0
                city_result.errors.append(f"Commit failed: {e}")

    return results


async def run_combined_ingestion() -> Tuple[List[IngestionResult], List[IngestionResult]]:
    """
    Run both weather and air quality ingestion.

    Returns tuple of (weather_results, air_quality_results).
    """
    weather_results = await run_weather_ingestion()
    air_quality_results = await run_air_quality_ingestion()
    return weather_results, air_quality_results
# ============================================================
# IoT Message Processing Pipeline (from remote contribution)
# ============================================================
# Import IoT processing components
try:
    from data_engineering.schemas.observation import Observation, RejectRecord
    from data_engineering.schemas.process_result import ProcessResult
    from data_engineering.adapters.iot import parse_iot_payload
    from data_engineering.validation.validator import validate_observation
    from data_engineering.normalization.normalizer import normalize_observation
    from data_engineering.deduplication.deduplicator import Deduplicator

    _IOT_PIPELINE_AVAILABLE = True
except ImportError:
    # IoT pipeline modules not yet available
    _IOT_PIPELINE_AVAILABLE = False
    Observation = None
    RejectRecord = None
    ProcessResult = None
    parse_iot_payload = None
    validate_observation = None
    normalize_observation = None
    Deduplicator = None

# Module-level deduplicator instance for IoT pipeline
_iot_deduplicator = Deduplicator() if _IOT_PIPELINE_AVAILABLE and Deduplicator else None


def process_iot_message(payload: Dict[str, Any]) -> "ProcessResult":
    """
    End-to-end processing of a single IoT message.

    Pipeline: Parse -> Validate -> Normalize -> Deduplicate

    Returns ProcessResult with accepted and rejected observations.
    """
    if not _IOT_PIPELINE_AVAILABLE:
        raise RuntimeError("IoT pipeline components not available. Ensure data_engineering schemas, adapters, validation, normalization, and deduplication modules are present.")

    result = ProcessResult(accepted=[], rejected=[])

    # 1. Adapt/Parse
    parsed_records, parsing_errors = parse_iot_payload(payload)
    for err in parsing_errors:
        result.add_rejection(err.raw_data, err.reason)

    # 2. Validate, Normalize, Deduplicate
    for obs in parsed_records:
        if not _iot_deduplicator.is_unique(obs):
            result.add_rejection(obs.model_dump(), "Duplicate record")
            continue

        is_valid, reason = validate_observation(obs)
        if not is_valid:
            result.add_rejection(obs.model_dump(), reason)
            continue

        normalized_obs = normalize_observation(obs)
        result.accepted.append(normalized_obs)

    return result


def reset_iot_deduplicator() -> None:
    """Reset the IoT deduplicator state (useful for testing)."""
    global _iot_deduplicator
    if _IOT_PIPELINE_AVAILABLE and Deduplicator:
        _iot_deduplicator = Deduplicator()