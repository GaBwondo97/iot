"""
Observation API routes.
"""

from datetime import datetime
from typing import Optional, Tuple
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import (
    get_observation_repo,
    pagination_params,
    validate_observation_id,
    validate_time_range,
)
from app.repositories import ObservationRepository
from app.schemas import ObservationCollectionResponse, ObservationDetailResponse, ObservationResponse

router = APIRouter(prefix="/observations", tags=["observations"])


@router.get("", response_model=ObservationCollectionResponse)
async def list_observations(
    city_id: Optional[UUID] = Query(None, description="Filter by city ID"),
    indicator_id: Optional[UUID] = Query(None, description="Filter by indicator ID"),
    source_type: Optional[str] = Query(None, description="Filter by source type (simulation, public_api)"),
    status: Optional[str] = Query(None, description="Filter by observation status (active, rejected, duplicate)"),
    time_range: Tuple[Optional[datetime], Optional[datetime]] = Depends(validate_time_range),
    pagination: dict = Depends(pagination_params),
    repo: ObservationRepository = Depends(get_observation_repo),
):
    """List observations with optional filtering and pagination."""
    start_time, end_time = time_range

    items = await repo.search(
        city_id=city_id,
        indicator_id=indicator_id,
        source_type=source_type,
        status=status,
        start_time=start_time,
        end_time=end_time,
        offset=pagination["offset"],
        limit=pagination["limit"],
    )
    total = await repo.count_filtered(
        city_id=city_id,
        indicator_id=indicator_id,
        source_type=source_type,
        status=status,
        start_time=start_time,
        end_time=end_time,
    )
    total_pages = (total + pagination["limit_param"] - 1) // pagination["limit_param"]

    return ObservationCollectionResponse(
        data=[ObservationResponse.model_validate(item) for item in items],
        pagination={
            "page": pagination["page"],
            "limit": pagination["limit_param"],
            "total": total,
            "total_pages": total_pages,
        },
    )


@router.get("/{observation_id}", response_model=ObservationDetailResponse)
async def get_observation(
    observation_id: UUID = Depends(validate_observation_id),
    repo: ObservationRepository = Depends(get_observation_repo),
):
    """Get a single observation by ID."""
    observation = await repo.get_by_id(observation_id)
    if observation is None:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=404,
            detail={"error": "not_found", "message": "Observation not found"},
        )
    return ObservationDetailResponse(data=ObservationResponse.model_validate(observation))