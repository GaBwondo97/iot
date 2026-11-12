"""
API dependencies and error handling for CityPulse AI.
"""

from datetime import datetime
from typing import Optional, Tuple
from uuid import UUID

from fastapi import Depends, HTTPException, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import AsyncSessionLocal, get_engine
from app.repositories import (
    AlertRepository,
    CityRepository,
    EnvironmentalIndicatorRepository,
    IoTDeviceRepository,
    ObservationRepository,
    RecommendationRepository,
    RiskAssessmentRepository,
)


# --- Database Dependency ---


async def get_db_session() -> AsyncSession:
    """
    Get database session from app state or raise 503 if unavailable.
    This wrapper provides a consistent error response when DB is not configured.
    """
    if get_engine() is None:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "database_unavailable",
                "message": "Database is not configured or unavailable",
            },
        )
    try:
        async with AsyncSessionLocal() as session:
            yield session
    except RuntimeError as e:
        raise HTTPException(
            status_code=503,
            detail={
                "error": "database_unavailable",
                "message": "Database is not configured or unavailable",
            },
        ) from e


# --- Repository Dependencies ---


def get_city_repo(session: AsyncSession = Depends(get_db_session)) -> CityRepository:
    return CityRepository(session)


def get_indicator_repo(
    session: AsyncSession = Depends(get_db_session),
) -> EnvironmentalIndicatorRepository:
    return EnvironmentalIndicatorRepository(session)


def get_sensor_repo(
    session: AsyncSession = Depends(get_db_session),
) -> IoTDeviceRepository:
    return IoTDeviceRepository(session)


def get_observation_repo(
    session: AsyncSession = Depends(get_db_session),
) -> ObservationRepository:
    return ObservationRepository(session)


def get_assessment_repo(
    session: AsyncSession = Depends(get_db_session),
) -> RiskAssessmentRepository:
    return RiskAssessmentRepository(session)


def get_alert_repo(
    session: AsyncSession = Depends(get_db_session),
) -> AlertRepository:
    return AlertRepository(session)


def get_recommendation_repo(
    session: AsyncSession = Depends(get_db_session),
) -> RecommendationRepository:
    return RecommendationRepository(session)


# --- Common Query Parameters ---


def pagination_params(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    limit: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
) -> dict:
    """Extract and validate pagination parameters."""
    offset = (page - 1) * limit
    return {"offset": offset, "limit": limit, "page": page, "limit_param": limit}


# --- UUID Path Parameter Validation ---


def validate_city_id(city_id: UUID) -> UUID:
    """Validate city UUID path parameter - FastAPI handles 422 automatically."""
    return city_id


def validate_indicator_id(indicator_id: UUID) -> UUID:
    """Validate indicator UUID path parameter - FastAPI handles 422 automatically."""
    return indicator_id


def validate_sensor_id(sensor_id: UUID) -> UUID:
    """Validate sensor UUID path parameter - FastAPI handles 422 automatically."""
    return sensor_id


def validate_observation_id(observation_id: UUID) -> UUID:
    """Validate observation UUID path parameter - FastAPI handles 422 automatically."""
    return observation_id


def validate_assessment_id(assessment_id: UUID) -> UUID:
    """Validate assessment UUID path parameter - FastAPI handles 422 automatically."""
    return assessment_id


def validate_alert_id(alert_id: UUID) -> UUID:
    """Validate alert UUID path parameter - FastAPI handles 422 automatically."""
    return alert_id


def validate_recommendation_id(recommendation_id: UUID) -> UUID:
    """Validate recommendation UUID path parameter - FastAPI handles 422 automatically."""
    return recommendation_id


# --- Time Range Validation ---


def validate_time_range(
    start_time: Optional[datetime] = Query(None, description="Start time (ISO 8601, timezone-aware)"),
    end_time: Optional[datetime] = Query(None, description="End time (ISO 8601, timezone-aware)"),
) -> Tuple[Optional[datetime], Optional[datetime]]:
    """Validate that start_time <= end_time if both provided."""
    if start_time and end_time and start_time > end_time:
        raise HTTPException(
            status_code=422,
            detail={
                "error": "invalid_date_range",
                "message": "start_time must be less than or equal to end_time",
            },
        )
    return start_time, end_time