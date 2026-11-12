import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import env_config
from app.api.routes.health import router as health_router
from app.api.routes.cities import router as cities_router
from app.api.routes.indicators import router as indicators_router
from app.api.routes.sensors import router as sensors_router
from app.api.routes.observations import router as observations_router
from app.api.routes.assessments import router as assessments_router
from app.api.routes.alerts import router as alerts_router
from app.api.routes.recommendations import router as recommendations_router
from app.db.session import init_db, close_db

log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """FastAPI lifespan: initialize DB on startup, dispose on shutdown."""
    log.info("Application starting up")
    init_db()
    yield
    log.info("Application shutting down")
    await close_db()


app = FastAPI(
    title=env_config.app_name,
    description=env_config.app_description,
    version=env_config.app_version,
    lifespan=lifespan,
)

# CORS: allow the exact dev origins (Vite serves on 5173, and 5174 when 5173 is busy).
# No wildcard — explicit list only. allow_credentials stays off (no cookie auth in Phase 1).
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174",
    ],
    allow_methods=["GET", "OPTIONS"],
    allow_headers=["*"],
    allow_credentials=False,
)

@app.get("/")
async def root():
    return {
        "name": env_config.app_name,
        "description": env_config.app_description,
        "version": env_config.app_version,
        "status": "running"
    }

@app.get("/health")
async def health():
    return {"status": "healthy", "service": "citypulse-backend"}

# Include all API routers under /api/v1
app.include_router(health_router, prefix="/api/v1")
app.include_router(cities_router, prefix="/api/v1")
app.include_router(indicators_router, prefix="/api/v1")
app.include_router(sensors_router, prefix="/api/v1")
app.include_router(observations_router, prefix="/api/v1")
app.include_router(assessments_router, prefix="/api/v1")
app.include_router(alerts_router, prefix="/api/v1")
app.include_router(recommendations_router, prefix="/api/v1")
