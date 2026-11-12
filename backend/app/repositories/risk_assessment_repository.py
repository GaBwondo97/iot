"""
Risk Assessment repository with filters and pagination.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import RiskAssessment
from app.repositories.base import BaseRepository


class RiskAssessmentRepository(BaseRepository[RiskAssessment]):
    """Repository for RiskAssessment operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, RiskAssessment)

    async def get_by_city(
        self,
        city_id: UUID,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> List[RiskAssessment]:
        """Get risk assessments by city with time ordering."""
        offset, limit = self._validate_pagination(offset, limit)
        result = await self.session.execute(
            select(RiskAssessment)
            .where(RiskAssessment.city_id == city_id)
            .order_by(RiskAssessment.assessed_at.desc(), RiskAssessment.id.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_indicator(
        self,
        indicator_id: UUID,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> List[RiskAssessment]:
        """Get risk assessments by indicator with time ordering."""
        offset, limit = self._validate_pagination(offset, limit)
        result = await self.session.execute(
            select(RiskAssessment)
            .where(RiskAssessment.indicator_id == indicator_id)
            .order_by(RiskAssessment.assessed_at.desc(), RiskAssessment.id.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def search(
        self,
        *,
        city_id: Optional[UUID] = None,
        indicator_id: Optional[UUID] = None,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> List[RiskAssessment]:
        """Search risk assessments with filters matching API contract."""
        offset, limit = self._validate_pagination(offset, limit)
        query = select(RiskAssessment)

        if city_id:
            query = query.where(RiskAssessment.city_id == city_id)
        if indicator_id:
            query = query.where(RiskAssessment.indicator_id == indicator_id)
        if status:
            query = query.where(RiskAssessment.status == status)
        if severity:
            query = query.where(RiskAssessment.severity == severity)
        if start_time:
            query = query.where(RiskAssessment.assessed_at >= start_time)
        if end_time:
            query = query.where(RiskAssessment.assessed_at <= end_time)

        query = query.order_by(RiskAssessment.assessed_at.desc(), RiskAssessment.id.desc()).offset(offset).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_filtered(
        self,
        *,
        city_id: Optional[UUID] = None,
        indicator_id: Optional[UUID] = None,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> int:
        """Count risk assessments with filters."""
        from sqlalchemy import func

        query = select(func.count()).select_from(RiskAssessment)

        if city_id:
            query = query.where(RiskAssessment.city_id == city_id)
        if indicator_id:
            query = query.where(RiskAssessment.indicator_id == indicator_id)
        if status:
            query = query.where(RiskAssessment.status == status)
        if severity:
            query = query.where(RiskAssessment.severity == severity)
        if start_time:
            query = query.where(RiskAssessment.assessed_at >= start_time)
        if end_time:
            query = query.where(RiskAssessment.assessed_at <= end_time)

        result = await self.session.execute(query)
        return result.scalar_one()