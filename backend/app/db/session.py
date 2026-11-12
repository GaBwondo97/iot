import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    async_sessionmaker,
    AsyncSession,
    AsyncEngine,
)

from app.core.config import env_config

log = logging.getLogger(__name__)

_engine: Optional[AsyncEngine] = None
_async_session_maker: Optional[async_sessionmaker] = None


def _create_engine() -> AsyncEngine:
    """Create async engine with pool_pre_ping."""
    return create_async_engine(
        env_config.database_url,
        pool_pre_ping=True,
    )


def init_db() -> None:
    """Initialize database engine and session factory. Call during app startup."""
    global _engine, _async_session_maker
    if not env_config.database_url:
        log.warning("DATABASE_URL not set; database features disabled")
        return
    if _engine is not None:
        return
    _engine = _create_engine()
    _async_session_maker = async_sessionmaker(
        bind=_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    log.info("Database engine initialized")


async def close_db() -> None:
    """Dispose database engine. Call during app shutdown."""
    global _engine, _async_session_maker
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _async_session_maker = None
        log.info("Database engine disposed")


def get_engine() -> Optional[AsyncEngine]:
    """Return the initialized engine, or None if not configured."""
    return _engine


class _AsyncSessionLocalProxy:
    def __call__(self, *args, **kwargs):
        if _async_session_maker is None:
            raise RuntimeError("Database not initialized. Check DATABASE_URL configuration.")
        return _async_session_maker(*args, **kwargs)

    def __getattr__(self, name):
        if _async_session_maker is None:
            raise RuntimeError("Database not initialized. Check DATABASE_URL configuration.")
        return getattr(_async_session_maker, name)


AsyncSessionLocal = _AsyncSessionLocalProxy()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency yielding a database session."""
    if _async_session_maker is None:
        raise RuntimeError("Database not initialized. Check DATABASE_URL configuration.")
    async with _async_session_maker() as session:
        yield session
