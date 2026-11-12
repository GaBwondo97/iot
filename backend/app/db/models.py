"""
SQLAlchemy 2.x Declarative Models for CityPulse AI.

Generated from database/migrations/001_initial_schema.sql (single source of truth).
Do not modify schema — changes require migration.
"""

import enum
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import (
    Boolean,
    DateTime,
    DECIMAL,
    Enum,
    ForeignKey,
    Index,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class City(Base):
    """Cities reference table."""
    __tablename__ = "cities"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=func.uuid_generate_v4(),
    )
    city_code: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    country_code: Mapped[str] = mapped_column(String(10), nullable=False)
    latitude: Mapped[float] = mapped_column(
        DECIMAL(9, 6), nullable=False
    )
    longitude: Mapped[float] = mapped_column(
        DECIMAL(9, 6), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.current_timestamp(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.current_timestamp(),
        nullable=False,
    )

    # Relationships
    iot_devices: Mapped[List["IoTDevice"]] = relationship(
        back_populates="city", cascade="all, delete-orphan"
    )
    observations: Mapped[List["Observation"]] = relationship(
        back_populates="city", cascade="all, delete-orphan"
    )
    risk_assessments: Mapped[List["RiskAssessment"]] = relationship(
        back_populates="city", cascade="all, delete-orphan"
    )
    alerts: Mapped[List["Alert"]] = relationship(
        back_populates="city", cascade="all, delete-orphan"
    )
    recommendations: Mapped[List["Recommendation"]] = relationship(
        back_populates="city", cascade="all, delete-orphan"
    )


class EnvironmentalIndicator(Base):
    """Environmental indicators reference table."""
    __tablename__ = "environmental_indicators"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=func.uuid_generate_v4(),
    )
    indicator_code: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False
    )
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    unit: Mapped[str] = mapped_column(String(30), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.current_timestamp(),
        nullable=False,
    )

    # Relationships
    observations: Mapped[List["Observation"]] = relationship(
        back_populates="indicator", cascade="all, delete-orphan"
    )
    risk_assessments: Mapped[List["RiskAssessment"]] = relationship(
        back_populates="indicator", cascade="all, delete-orphan"
    )


class IoTDeviceStatus(str, enum.Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    DEGRADED = "degraded"


class IoTDevice(Base):
    """IoT devices reference table."""
    __tablename__ = "iot_devices"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=func.uuid_generate_v4(),
    )
    device_id: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False
    )
    city_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("cities.id", ondelete="CASCADE"),
        nullable=False,
    )
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[IoTDeviceStatus] = mapped_column(
        String(30),
        default=IoTDeviceStatus.ONLINE,
        nullable=False,
    )
    last_seen: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.current_timestamp(),
        nullable=False,
    )

    # Relationships
    city: Mapped["City"] = relationship(back_populates="iot_devices")
    observations: Mapped[List["Observation"]] = relationship(
        back_populates="iot_device"
    )


class ObservationStatus(str, enum.Enum):
    ACTIVE = "active"
    REJECTED = "rejected"
    DUPLICATE = "duplicate"


class ObservationSeverity(str, enum.Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class Observation(Base):
    """Unified observations table."""
    __tablename__ = "observations"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=func.uuid_generate_v4(),
    )
    city_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("cities.id", ondelete="CASCADE"),
        nullable=False,
    )
    indicator_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("environmental_indicators.id", ondelete="CASCADE"),
        nullable=False,
    )
    iot_device_id: Mapped[Optional[UUID]] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("iot_devices.id", ondelete="SET NULL"),
        nullable=True,
    )
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    source_name: Mapped[str] = mapped_column(String(100), nullable=False)
    record_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.current_timestamp(),
        nullable=False,
    )
    value: Mapped[Optional[float]] = mapped_column(
        DECIMAL(12, 4), nullable=True
    )
    status: Mapped[ObservationStatus] = mapped_column(
        String(30),
        default=ObservationStatus.ACTIVE,
        nullable=False,
    )
    severity: Mapped[Optional[ObservationSeverity]] = mapped_column(
        String(30),
        nullable=True,
    )
    confidence: Mapped[Optional[float]] = mapped_column(
        DECIMAL(3, 2), nullable=True
    )
    raw_payload: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Constraints
    __table_args__ = (
        UniqueConstraint(
            "city_id",
            "indicator_id",
            "observed_at",
            "source_type",
            name="uq_observation_record",
        ),
        Index("idx_obs_city_time", "city_id", "observed_at"),
        Index("idx_obs_indicator_time", "indicator_id", "observed_at"),
        Index("idx_obs_source", "source_type"),
    )

    # Relationships
    city: Mapped["City"] = relationship(back_populates="observations")
    indicator: Mapped["EnvironmentalIndicator"] = relationship(back_populates="observations")
    iot_device: Mapped[Optional["IoTDevice"]] = relationship(back_populates="observations")


class RiskAssessmentStatus(str, enum.Enum):
    ANALYZED = "analyzed"
    PARTIAL = "partial"
    INSUFFICIENT_DATA = "insufficient_data"


class RiskSeverity(str, enum.Enum):
    LOW = "low"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"
    INSUFFICIENT_DATA = "Insufficient Data"


class RiskAssessment(Base):
    """Risk assessments table."""
    __tablename__ = "risk_assessments"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=func.uuid_generate_v4(),
    )
    city_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("cities.id", ondelete="CASCADE"),
        nullable=False,
    )
    indicator_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("environmental_indicators.id", ondelete="CASCADE"),
        nullable=False,
    )
    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    status: Mapped[RiskAssessmentStatus] = mapped_column(
        String(30),
        nullable=False,
    )
    risk_score: Mapped[Optional[float]] = mapped_column(
        DECIMAL(3, 2), nullable=True
    )
    severity: Mapped[Optional[RiskSeverity]] = mapped_column(
        String(30),
        nullable=True,
    )
    confidence: Mapped[Optional[float]] = mapped_column(
        DECIMAL(3, 2), nullable=True
    )
    assessment_text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    assessed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.current_timestamp(),
        nullable=False,
    )
    data_points_count: Mapped[int] = mapped_column(default=0, nullable=False)
    missing_indicators: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)

    # Constraints
    __table_args__ = (
        Index("idx_risk_city_time", "city_id", "assessed_at"),
    )

    # Relationships
    city: Mapped["City"] = relationship(back_populates="risk_assessments")
    indicator: Mapped["EnvironmentalIndicator"] = relationship(back_populates="risk_assessments")
    alerts: Mapped[List["Alert"]] = relationship(
        back_populates="risk_assessment", cascade="all, delete-orphan"
    )
    recommendations: Mapped[List["Recommendation"]] = relationship(
        back_populates="risk_assessment", cascade="all, delete-orphan"
    )


class AlertStatus(str, enum.Enum):
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"


class Alert(Base):
    """Alerts table."""
    __tablename__ = "alerts"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=func.uuid_generate_v4(),
    )
    city_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("cities.id", ondelete="CASCADE"),
        nullable=False,
    )
    risk_assessment_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("risk_assessments.id", ondelete="CASCADE"),
        nullable=False,
    )
    severity: Mapped[RiskSeverity] = mapped_column(
        String(30),
        nullable=False,
    )
    message: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[AlertStatus] = mapped_column(
        String(30),
        default=AlertStatus.ACTIVE,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.current_timestamp(),
        nullable=False,
    )

    # Relationships
    city: Mapped["City"] = relationship(back_populates="alerts")
    risk_assessment: Mapped["RiskAssessment"] = relationship(back_populates="alerts")


class Recommendation(Base):
    """Recommendations table."""
    __tablename__ = "recommendations"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=func.uuid_generate_v4(),
    )
    city_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("cities.id", ondelete="CASCADE"),
        nullable=False,
    )
    risk_assessment_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("risk_assessments.id", ondelete="CASCADE"),
        nullable=False,
    )
    recommendation_text: Mapped[str] = mapped_column(Text, nullable=False)
    action_required: Mapped[bool] = mapped_column(
        Boolean, default=False, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.current_timestamp(),
        nullable=False,
    )

    # Relationships
    city: Mapped["City"] = relationship(back_populates="recommendations")
    risk_assessment: Mapped["RiskAssessment"] = relationship(back_populates="recommendations")


class IngestionRejectionLog(Base):
    """Ingestion audit / rejection log table."""
    __tablename__ = "ingestion_rejection_logs"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        primary_key=True,
        server_default=func.uuid_generate_v4(),
    )
    source_type: Mapped[str] = mapped_column(String(50), nullable=False)
    reason_code: Mapped[str] = mapped_column(String(100), nullable=False)
    details: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    rejected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.current_timestamp(),
        nullable=False,
    )