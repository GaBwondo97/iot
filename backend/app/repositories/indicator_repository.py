"""
Environmental Indicator repository with filters and pagination.
"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import EnvironmentalIndicator
from app.repositories.base import BaseRepository


class EnvironmentalIndicatorRepository(BaseRepository[EnvironmentalIndicator]):
    """Repository for EnvironmentalIndicator operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, EnvironmentalIndicator)

    async def get_by_indicator_code(self, indicator_code: str) -> Optional[EnvironmentalIndicator]:
        """Get indicator by indicator_code."""
        result = await self.session.execute(
            select(EnvironmentalIndicator).where(
                EnvironmentalIndicator.indicator_code == indicator_code
            )
        )
        return result.scalar_one_or_none()

    async def get_by_category(self, category: str) -> List[EnvironmentalIndicator]:
        """Get indicators by category."""
        result = await self.session.execute(
            select(EnvironmentalIndicator).where(
                EnvironmentalIndicator.category == category
            )
        )
        return list(result.scalars().all())

    async def search(
        self,
        *,
        category: Optional[str] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> List[EnvironmentalIndicator]:
        """Search indicators with optional filters."""
        offset, limit = self._validate_pagination(offset, limit)
        query = select(EnvironmentalIndicator)

        if category:
            query = query.where(EnvironmentalIndicator.category == category)

        query = query.order_by(EnvironmentalIndicator.created_at.desc(), EnvironmentalIndicator.id.desc()).offset(offset).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_filtered(
        self,
        *,
        category: Optional[str] = None,
    ) -> int:
        """Count indicators with optional filters."""
        from sqlalchemy import func

        query = select(func.count()).select_from(EnvironmentalIndicator)

        if category:
            query = query.where(EnvironmentalIndicator.category == category)

        result = await self.session.execute(query)
        return result.scalar_one()