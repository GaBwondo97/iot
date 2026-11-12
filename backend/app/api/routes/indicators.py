"""
Indicator API routes.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import (
    get_indicator_repo,
    pagination_params,
    validate_indicator_id,
)
from app.repositories import EnvironmentalIndicatorRepository
from app.schemas import IndicatorCollectionResponse, IndicatorDetailResponse, IndicatorResponse

router = APIRouter(prefix="/indicators", tags=["indicators"])


@router.get("", response_model=IndicatorCollectionResponse)
async def list_indicators(
    category: Optional[str] = Query(None, description="Filter by indicator category"),
    pagination: dict = Depends(pagination_params),
    repo: EnvironmentalIndicatorRepository = Depends(get_indicator_repo),
):
    """List environmental indicators with optional filtering and pagination."""
    items = await repo.search(
        category=category,
        offset=pagination["offset"],
        limit=pagination["limit"],
    )
    total = await repo.count_filtered(category=category)
    total_pages = (total + pagination["limit_param"] - 1) // pagination["limit_param"]

    return IndicatorCollectionResponse(
        data=[IndicatorResponse.model_validate(item) for item in items],
        pagination={
            "page": pagination["page"],
            "limit": pagination["limit_param"],
            "total": total,
            "total_pages": total_pages,
        },
    )


@router.get("/{indicator_id}", response_model=IndicatorDetailResponse)
async def get_indicator(
    indicator_id: UUID = Depends(validate_indicator_id),
    repo: EnvironmentalIndicatorRepository = Depends(get_indicator_repo),
):
    """Get a single indicator by ID."""
    indicator = await repo.get_by_id(indicator_id)
    if indicator is None:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=404,
            detail={"error": "not_found", "message": "Indicator not found"},
        )
    return IndicatorDetailResponse(data=IndicatorResponse.model_validate(indicator))