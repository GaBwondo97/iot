import os
import sys
import pytest
from httpx import AsyncClient
from app.main import app
from app.db.session import init_db, close_db, AsyncSessionLocal

def test_import_session():
    """Verify session module exports expected items."""
    assert AsyncSessionLocal is not None
    print("Import test passed.")

@pytest.mark.asyncio
async def test_startup_no_db():
    """Verify app starts without DATABASE_URL."""
    os.environ["DATABASE_URL"] = ""
    init_db()
    try:
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.get("/")
            assert response.status_code == 200
            
            response = await ac.get("/health")
            assert response.status_code == 200
    finally:
        await close_db()
    print("Startup without DATABASE_URL passed.")

@pytest.mark.asyncio
async def test_startup_with_invalid_db():
    """Verify app handles non-empty invalid URL (engine lazy-init or error on access)."""
    os.environ["DATABASE_URL"] = "postgresql://invalid"
    init_db()
    try:
        # Engine might not error until access
        async with AsyncClient(app=app, base_url="http://test") as ac:
            response = await ac.get("/")
            assert response.status_code == 200
    finally:
        await close_db()
    print("Startup with invalid DATABASE_URL passed.")
