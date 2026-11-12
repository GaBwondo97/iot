"""
Pydantic response schemas for CityPulse AI API.

These schemas define the public API response format, separate from
internal database models.
"""

from datetime import datetime
from typing import Any, Generic, List, Optional, TypeVar
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


T = TypeVar("T")


class PaginationMeta(BaseModel):
    """Pagination metadata for collection responses."""

    page: int = Field(ge=1, description="Current page number (1-indexed)")
    limit: int = Field(ge=1, le=100, description="Items per page")
    total: int = Field(ge=0, description="Total number of items across all pages")
    total_pages: int = Field(ge=0, description="Total number of pages")

    model_config = ConfigDict(from_attributes=True)


class CollectionResponse(BaseModel, Generic[T]):
    """Standard collection response envelope with pagination."""

    data: List[T] = Field(default_factory=list)
    pagination: PaginationMeta

    model_config = ConfigDict(from_attributes=True)


class DetailResponse(BaseModel, Generic[T]):
    """Standard detail response envelope."""

    data: T

    model_config = ConfigDict(from_attributes=True)


# --- City Schemas ---


class CityResponse(BaseModel):
    """City detail response."""

    id: UUID
    city_code: str
    name: str
    country_code: str
    latitude: float
    longitude: float
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class CityCollectionResponse(CollectionResponse[CityResponse]):
    """City list response with pagination."""

    pass


class CityDetailResponse(DetailResponse[CityResponse]):
    """Single city response."""

    pass


# --- Indicator Schemas ---


class IndicatorResponse(BaseModel):
    """Environmental indicator detail response."""

    id: UUID
    indicator_code: str
    name: str
    category: str
    unit: str
    description: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class IndicatorCollectionResponse(CollectionResponse[IndicatorResponse]):
    """Indicator list response with pagination."""

    pass


class IndicatorDetailResponse(DetailResponse[IndicatorResponse]):
    """Single indicator response."""

    pass


# --- IoT Device / Sensor Schemas ---


class SensorResponse(BaseModel):
    """IoT device (sensor) detail response."""

    id: UUID
    device_id: str
    city_id: UUID
    category: str
    status: str
    last_seen: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SensorCollectionResponse(CollectionResponse[SensorResponse]):
    """Sensor list response with pagination."""

    pass


class SensorDetailResponse(DetailResponse[SensorResponse]):
    """Single sensor response."""

    pass


# --- Observation Schemas ---


class ObservationResponse(BaseModel):
    """Observation detail response."""

    id: UUID
    city_id: UUID
    indicator_id: UUID
    iot_device_id: Optional[UUID] = None
    source_type: str
    source_name: str
    record_id: Optional[str] = None
    observed_at: datetime
    ingested_at: datetime
    value: Optional[float] = None
    status: str
    severity: Optional[str] = None
    confidence: Optional[float] = None
    raw_payload: Optional[dict] = None

    model_config = ConfigDict(from_attributes=True)


class ObservationCollectionResponse(CollectionResponse[ObservationResponse]):
    """Observation list response with pagination."""

    pass


class ObservationDetailResponse(DetailResponse[ObservationResponse]):
    """Single observation response."""

    pass


# --- Risk Assessment Schemas ---


class RiskAssessmentResponse(BaseModel):
    """Risk assessment detail response."""

    id: UUID
    city_id: UUID
    indicator_id: UUID
    observed_at: datetime
    status: str
    risk_score: Optional[float] = None
    severity: Optional[str] = None
    confidence: Optional[float] = None
    assessment_text: Optional[str] = None
    assessed_at: datetime
    data_points_count: int
    missing_indicators: Optional[dict] = None

    model_config = ConfigDict(from_attributes=True)


class RiskAssessmentCollectionResponse(CollectionResponse[RiskAssessmentResponse]):
    """Risk assessment list response with pagination."""

    pass


class RiskAssessmentDetailResponse(DetailResponse[RiskAssessmentResponse]):
    """Single risk assessment response."""

    pass


# --- Alert Schemas ---


class AlertResponse(BaseModel):
    """Alert detail response."""

    id: UUID
    city_id: UUID
    risk_assessment_id: UUID
    severity: str
    message: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AlertCollectionResponse(CollectionResponse[AlertResponse]):
    """Alert list response with pagination."""

    pass


class AlertDetailResponse(DetailResponse[AlertResponse]):
    """Single alert response."""

    pass


# --- Recommendation Schemas ---


class RecommendationResponse(BaseModel):
    """Recommendation detail response."""

    id: UUID
    city_id: UUID
    risk_assessment_id: UUID
    recommendation_text: str
    action_required: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RecommendationCollectionResponse(CollectionResponse[RecommendationResponse]):
    """Recommendation list response with pagination."""

    pass


class RecommendationDetailResponse(DetailResponse[RecommendationResponse]):
    """Single recommendation response."""

    pass