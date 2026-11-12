"""
City API routes.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import (
    get_city_repo,
    pagination_params,
    validate_time_range,
    validate_city_id,
)
from app.repositories import CityRepository
from app.schemas import CityCollectionResponse, CityDetailResponse, CityResponse

router = APIRouter(prefix="/cities", tags=["cities"])


@router.get("", response_model=CityCollectionResponse)
async def list_cities(
    country_code: Optional[str] = Query(None, description="Filter by country code (ISO 3166-1 alpha-2)"),
    pagination: dict = Depends(pagination_params),
    repo: CityRepository = Depends(get_city_repo),
):
    """List cities with optional filtering and pagination."""
    items = await repo.search(
        country_code=country_code,
        offset=pagination["offset"],
        limit=pagination["limit"],
    )
    total = await repo.count_filtered(country_code=country_code)
    total_pages = (total + pagination["limit_param"] - 1) // pagination["limit_param"]

    return CityCollectionResponse(
        data=[CityResponse.model_validate(item) for item in items],
        pagination={
            "page": pagination["page"],
            "limit": pagination["limit_param"],
            "total": total,
            "total_pages": total_pages,
        },
    )


@router.get("/{city_id}", response_model=CityDetailResponse)
async def get_city(
    city_id: UUID = Depends(validate_city_id),
    repo: CityRepository = Depends(get_city_repo),
):
    """Get a single city by ID."""
    city = await repo.get_by_id(city_id)
    if city is None:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=404,
            detail={"error": "not_found", "message": "City not found"},
        )
    return CityDetailResponse(data=CityResponse.model_validate(city))