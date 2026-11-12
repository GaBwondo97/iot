"""
Sensor (IoT Device) API routes.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import (
    get_sensor_repo,
    pagination_params,
    validate_sensor_id,
)
from app.repositories import IoTDeviceRepository
from app.schemas import SensorCollectionResponse, SensorDetailResponse, SensorResponse

router = APIRouter(prefix="/sensors", tags=["sensors"])


@router.get("", response_model=SensorCollectionResponse)
async def list_sensors(
    city_id: Optional[UUID] = Query(None, description="Filter by city ID"),
    category: Optional[str] = Query(None, description="Filter by sensor category"),
    status: Optional[str] = Query(None, description="Filter by sensor status (online, offline, degraded)"),
    pagination: dict = Depends(pagination_params),
    repo: IoTDeviceRepository = Depends(get_sensor_repo),
):
    """List IoT devices (sensors) with optional filtering and pagination."""
    items = await repo.search(
        city_id=city_id,
        category=category,
        status=status,
        offset=pagination["offset"],
        limit=pagination["limit"],
    )
    total = await repo.count_filtered(city_id=city_id, category=category, status=status)
    total_pages = (total + pagination["limit_param"] - 1) // pagination["limit_param"]

    return SensorCollectionResponse(
        data=[SensorResponse.model_validate(item) for item in items],
        pagination={
            "page": pagination["page"],
            "limit": pagination["limit_param"],
            "total": total,
            "total_pages": total_pages,
        },
    )


@router.get("/{sensor_id}", response_model=SensorDetailResponse)
async def get_sensor(
    sensor_id: UUID = Depends(validate_sensor_id),
    repo: IoTDeviceRepository = Depends(get_sensor_repo),
):
    """Get a single sensor by ID."""
    sensor = await repo.get_by_id(sensor_id)
    if sensor is None:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=404,
            detail={"error": "not_found", "message": "Sensor not found"},
        )
    return SensorDetailResponse(data=SensorResponse.model_validate(sensor))