"""
Observation repository with filters and pagination.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Observation
from app.repositories.base import BaseRepository


class ObservationRepository(BaseRepository[Observation]):
    """Repository for Observation operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Observation)

    async def get_by_city(
        self,
        city_id: UUID,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> List[Observation]:
        """Get observations by city with time ordering."""
        offset, limit = self._validate_pagination(offset, limit)
        result = await self.session.execute(
            select(Observation)
            .where(Observation.city_id == city_id)
            .order_by(Observation.observed_at.desc(), Observation.id.desc())
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
    ) -> List[Observation]:
        """Get observations by indicator with time ordering."""
        offset, limit = self._validate_pagination(offset, limit)
        result = await self.session.execute(
            select(Observation)
            .where(Observation.indicator_id == indicator_id)
            .order_by(Observation.observed_at.desc(), Observation.id.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def search(
        self,
        *,
        city_id: Optional[UUID] = None,
        indicator_id: Optional[UUID] = None,
        source_type: Optional[str] = None,
        status: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> List[Observation]:
        """Search observations with filters matching API contract."""
        offset, limit = self._validate_pagination(offset, limit)
        query = select(Observation)

        if city_id:
            query = query.where(Observation.city_id == city_id)
        if indicator_id:
            query = query.where(Observation.indicator_id == indicator_id)
        if source_type:
            query = query.where(Observation.source_type == source_type)
        if status:
            query = query.where(Observation.status == status)
        if start_time:
            query = query.where(Observation.observed_at >= start_time)
        if end_time:
            query = query.where(Observation.observed_at <= end_time)

        query = query.order_by(Observation.observed_at.desc(), Observation.id.desc()).offset(offset).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_filtered(
        self,
        *,
        city_id: Optional[UUID] = None,
        indicator_id: Optional[UUID] = None,
        source_type: Optional[str] = None,
        status: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
    ) -> int:
        """Count observations with filters."""
        from sqlalchemy import func

        query = select(func.count()).select_from(Observation)

        if city_id:
            query = query.where(Observation.city_id == city_id)
        if indicator_id:
            query = query.where(Observation.indicator_id == indicator_id)
        if source_type:
            query = query.where(Observation.source_type == source_type)
        if status:
            query = query.where(Observation.status == status)
        if start_time:
            query = query.where(Observation.observed_at >= start_time)
        if end_time:
            query = query.where(Observation.observed_at <= end_time)

        result = await self.session.execute(query)
        return result.scalar_one()