"""
City repository with filters and pagination.
"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import City
from app.repositories.base import BaseRepository


class CityRepository(BaseRepository[City]):
    """Repository for City operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, City)

    async def get_by_city_code(self, city_code: str) -> Optional[City]:
        """Get city by city_code."""
        result = await self.session.execute(
            select(City).where(City.city_code == city_code)
        )
        return result.scalar_one_or_none()

    async def get_by_country_code(self, country_code: str) -> List[City]:
        """Get cities by country code."""
        result = await self.session.execute(
            select(City).where(City.country_code == country_code)
        )
        return list(result.scalars().all())

    async def search(
        self,
        *,
        country_code: Optional[str] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> List[City]:
        """Search cities with optional filters."""
        offset, limit = self._validate_pagination(offset, limit)
        query = select(City)

        if country_code:
            query = query.where(City.country_code == country_code)

        query = query.order_by(City.created_at.desc(), City.id.desc()).offset(offset).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_filtered(
        self,
        *,
        country_code: Optional[str] = None,
    ) -> int:
        """Count cities with optional filters."""
        from sqlalchemy import func

        query = select(func.count()).select_from(City)

        if country_code:
            query = query.where(City.country_code == country_code)

        result = await self.session.execute(query)
        return result.scalar_one()