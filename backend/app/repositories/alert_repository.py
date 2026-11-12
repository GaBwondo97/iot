"""
Alert repository with filters and pagination.
"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Alert
from app.repositories.base import BaseRepository


class AlertRepository(BaseRepository[Alert]):
    """Repository for Alert operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Alert)

    async def get_by_city(
        self,
        city_id: UUID,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> List[Alert]:
        """Get alerts by city with time ordering."""
        offset, limit = self._validate_pagination(offset, limit)
        result = await self.session.execute(
            select(Alert)
            .where(Alert.city_id == city_id)
            .order_by(Alert.created_at.desc(), Alert.id.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_risk_assessment(self, risk_assessment_id: UUID) -> List[Alert]:
        """Get alerts by risk assessment."""
        result = await self.session.execute(
            select(Alert).where(Alert.risk_assessment_id == risk_assessment_id)
        )
        return list(result.scalars().all())

    async def search(
        self,
        *,
        city_id: Optional[UUID] = None,
        status: Optional[str] = None,
        severity: Optional[str] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> List[Alert]:
        """Search alerts with filters."""
        offset, limit = self._validate_pagination(offset, limit)
        query = select(Alert)

        if city_id:
            query = query.where(Alert.city_id == city_id)
        if status:
            query = query.where(Alert.status == status)
        if severity:
            query = query.where(Alert.severity == severity)

        query = query.order_by(Alert.created_at.desc(), Alert.id.desc()).offset(offset).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_filtered(
        self,
        *,
        city_id: Optional[UUID] = None,
        status: Optional[str] = None,
        severity: Optional[str] = None,
    ) -> int:
        """Count alerts with filters."""
        from sqlalchemy import func

        query = select(func.count()).select_from(Alert)

        if city_id:
            query = query.where(Alert.city_id == city_id)
        if status:
            query = query.where(Alert.status == status)
        if severity:
            query = query.where(Alert.severity == severity)

        result = await self.session.execute(query)
        return result.scalar_one()