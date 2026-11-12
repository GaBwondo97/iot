"""
Recommendation repository with filters and pagination.
"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Recommendation
from app.repositories.base import BaseRepository


class RecommendationRepository(BaseRepository[Recommendation]):
    """Repository for Recommendation operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, Recommendation)

    async def get_by_city(
        self,
        city_id: UUID,
        *,
        offset: int = 0,
        limit: int = 20,
    ) -> List[Recommendation]:
        """Get recommendations by city with time ordering."""
        offset, limit = self._validate_pagination(offset, limit)
        result = await self.session.execute(
            select(Recommendation)
            .where(Recommendation.city_id == city_id)
            .order_by(Recommendation.created_at.desc(), Recommendation.id.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_risk_assessment(self, risk_assessment_id: UUID) -> List[Recommendation]:
        """Get recommendations by risk assessment."""
        result = await self.session.execute(
            select(Recommendation).where(
                Recommendation.risk_assessment_id == risk_assessment_id
            )
        )
        return list(result.scalars().all())

    async def search(
        self,
        *,
        city_id: Optional[UUID] = None,
        risk_assessment_id: Optional[UUID] = None,
        action_required: Optional[bool] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> List[Recommendation]:
        """Search recommendations with filters."""
        offset, limit = self._validate_pagination(offset, limit)
        query = select(Recommendation)

        if city_id:
            query = query.where(Recommendation.city_id == city_id)
        if risk_assessment_id:
            query = query.where(Recommendation.risk_assessment_id == risk_assessment_id)
        if action_required is not None:
            query = query.where(Recommendation.action_required == action_required)

        query = query.order_by(Recommendation.created_at.desc(), Recommendation.id.desc()).offset(offset).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_filtered(
        self,
        *,
        city_id: Optional[UUID] = None,
        risk_assessment_id: Optional[UUID] = None,
        action_required: Optional[bool] = None,
    ) -> int:
        """Count recommendations with filters."""
        from sqlalchemy import func

        query = select(func.count()).select_from(Recommendation)

        if city_id:
            query = query.where(Recommendation.city_id == city_id)
        if risk_assessment_id:
            query = query.where(Recommendation.risk_assessment_id == risk_assessment_id)
        if action_required is not None:
            query = query.where(Recommendation.action_required == action_required)

        result = await self.session.execute(query)
        return result.scalar_one()