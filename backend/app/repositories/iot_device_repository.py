"""
IoT Device repository with filters and pagination.
"""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import IoTDevice
from app.repositories.base import BaseRepository


class IoTDeviceRepository(BaseRepository[IoTDevice]):
    """Repository for IoTDevice operations."""

    def __init__(self, session: AsyncSession):
        super().__init__(session, IoTDevice)

    async def get_by_device_id(self, device_id: str) -> Optional[IoTDevice]:
        """Get device by device_id."""
        result = await self.session.execute(
            select(IoTDevice).where(IoTDevice.device_id == device_id)
        )
        return result.scalar_one_or_none()

    async def get_by_city(self, city_id: UUID) -> List[IoTDevice]:
        """Get devices by city."""
        result = await self.session.execute(
            select(IoTDevice).where(IoTDevice.city_id == city_id)
        )
        return list(result.scalars().all())

    async def get_by_status(self, status: str) -> List[IoTDevice]:
        """Get devices by status."""
        result = await self.session.execute(
            select(IoTDevice).where(IoTDevice.status == status)
        )
        return list(result.scalars().all())

    async def search(
        self,
        *,
        city_id: Optional[UUID] = None,
        status: Optional[str] = None,
        category: Optional[str] = None,
        offset: int = 0,
        limit: int = 20,
    ) -> List[IoTDevice]:
        """Search devices with optional filters."""
        offset, limit = self._validate_pagination(offset, limit)
        query = select(IoTDevice)

        if city_id:
            query = query.where(IoTDevice.city_id == city_id)
        if status:
            query = query.where(IoTDevice.status == status)
        if category:
            query = query.where(IoTDevice.category == category)

        query = query.order_by(IoTDevice.created_at.desc(), IoTDevice.id.desc()).offset(offset).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def count_filtered(
        self,
        *,
        city_id: Optional[UUID] = None,
        status: Optional[str] = None,
        category: Optional[str] = None,
    ) -> int:
        """Count devices with optional filters."""
        from sqlalchemy import func

        query = select(func.count()).select_from(IoTDevice)

        if city_id:
            query = query.where(IoTDevice.city_id == city_id)
        if status:
            query = query.where(IoTDevice.status == status)
        if category:
            query = query.where(IoTDevice.category == category)

        result = await self.session.execute(query)
        return result.scalar_one()