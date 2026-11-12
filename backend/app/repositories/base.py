"""
Base repository with common CRUD and pagination utilities.
"""

from typing import Generic, List, Optional, Tuple, Type, TypeVar
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import ColumnProperty

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """Base repository with common operations."""

    def __init__(self, session: AsyncSession, model: Type[T]):
        self.session = session
        self.model = model
        self._default_order_col = getattr(model, "created_at", None)
        self._primary_key_col = getattr(model, "id", None)

    def _validate_pagination(self, offset: int, limit: int) -> Tuple[int, int]:
        """Validate and normalize pagination parameters."""
        if offset < 0:
            offset = 0
        if limit > 100:
            limit = 100
        if limit < 1:
            limit = 20
        return offset, limit

    def _build_order_by(self, order_by: str, order_desc: bool = True):
        """Build safe ordering with primary key tie-breaker."""
        order_col = getattr(self.model, order_by, None)
        if order_col is None or not isinstance(order_col.property, ColumnProperty):
            order_col = self._default_order_col

        if order_col is None:
            order_col = self._primary_key_col

        if order_desc:
            primary_order = order_col.desc()
        else:
            primary_order = order_col.asc()

        # Add primary key tie-breaker for deterministic ordering
        if self._primary_key_col is not None and order_col != self._primary_key_col:
            return [primary_order, self._primary_key_col.desc()]
        return [primary_order]

    async def get_by_id(self, id: UUID) -> Optional[T]:
        """Get a single record by primary key."""
        result = await self.session.execute(
            select(self.model).where(self.model.id == id)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        *,
        offset: int = 0,
        limit: int = 20,
        order_by: str = "created_at",
        order_desc: bool = True,
    ) -> List[T]:
        """Get paginated records with deterministic ordering."""
        offset, limit = self._validate_pagination(offset, limit)
        order_clauses = self._build_order_by(order_by, order_desc)

        result = await self.session.execute(
            select(self.model).order_by(*order_clauses).offset(offset).limit(limit)
        )
        return list(result.scalars().all())

    async def count(self) -> int:
        """Get total count of records."""
        result = await self.session.execute(
            select(func.count()).select_from(self.model)
        )
        return result.scalar_one()

    async def create(self, **kwargs) -> T:
        """Create a new record."""
        obj = self.model(**kwargs)
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def update(self, obj: T, **kwargs) -> T:
        """Update an existing record - only mapped columns, no PK changes."""
        # Prevent updating primary key and relationships
        protected_attrs = {"id"}
        for rel in self.model.__mapper__.relationships:
            protected_attrs.add(rel.key)

        for key, value in kwargs.items():
            if key in protected_attrs:
                continue
            if hasattr(obj, key):
                attr = getattr(self.model, key, None)
                # Only allow updates to mapped columns (not relationships)
                if attr is not None and isinstance(attr.property, ColumnProperty):
                    setattr(obj, key, value)

        await self.session.flush()
        await self.session.refresh(obj)
        return obj