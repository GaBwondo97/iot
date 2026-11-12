"""
Recommendation API routes.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import (
    get_recommendation_repo,
    pagination_params,
    validate_recommendation_id,
)
from app.repositories import RecommendationRepository
from app.schemas import (
    RecommendationCollectionResponse,
    RecommendationDetailResponse,
    RecommendationResponse,
)

router = APIRouter(prefix="/recommendations", tags=["recommendations"])


@router.get("", response_model=RecommendationCollectionResponse)
async def list_recommendations(
    city_id: Optional[UUID] = Query(None, description="Filter by city ID"),
    risk_assessment_id: Optional[UUID] = Query(None, description="Filter by risk assessment ID"),
    action_required: Optional[bool] = Query(None, description="Filter by action_required flag"),
    pagination: dict = Depends(pagination_params),
    repo: RecommendationRepository = Depends(get_recommendation_repo),
):
    """List recommendations with optional filtering and pagination."""
    items = await repo.search(
        city_id=city_id,
        risk_assessment_id=risk_assessment_id,
        action_required=action_required,
        offset=pagination["offset"],
        limit=pagination["limit"],
    )
    total = await repo.count_filtered(city_id=city_id, risk_assessment_id=risk_assessment_id, action_required=action_required)
    total_pages = (total + pagination["limit_param"] - 1) // pagination["limit_param"]

    return RecommendationCollectionResponse(
        data=[RecommendationResponse.model_validate(item) for item in items],
        pagination={
            "page": pagination["page"],
            "limit": pagination["limit_param"],
            "total": total,
            "total_pages": total_pages,
        },
    )


@router.get("/{recommendation_id}", response_model=RecommendationDetailResponse)
async def get_recommendation(
    recommendation_id: UUID = Depends(validate_recommendation_id),
    repo: RecommendationRepository = Depends(get_recommendation_repo),
):
    """Get a single recommendation by ID."""
    recommendation = await repo.get_by_id(recommendation_id)
    if recommendation is None:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=404,
            detail={"error": "not_found", "message": "Recommendation not found"},
        )
    return RecommendationDetailResponse(data=RecommendationResponse.model_validate(recommendation))