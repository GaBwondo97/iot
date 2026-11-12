"""
API routes package exports.
"""

from app.api.routes.cities import router as cities_router
from app.api.routes.indicators import router as indicators_router
from app.api.routes.sensors import router as sensors_router
from app.api.routes.observations import router as observations_router
from app.api.routes.assessments import router as assessments_router
from app.api.routes.alerts import router as alerts_router
from app.api.routes.recommendations import router as recommendations_router
from app.api.routes.health import router as health_router

__all__ = [
    "cities_router",
    "indicators_router",
    "sensors_router",
    "observations_router",
    "assessments_router",
    "alerts_router",
    "recommendations_router",
    "health_router",
]