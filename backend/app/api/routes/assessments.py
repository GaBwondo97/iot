"""
Risk Assessment API routes.
"""

from datetime import datetime
from typing import Optional, Tuple
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import (
    get_assessment_repo,
    pagination_params,
    validate_assessment_id,
    validate_time_range,
)
from app.repositories import RiskAssessmentRepository
from app.schemas import (
    RiskAssessmentCollectionResponse,
    RiskAssessmentDetailResponse,
    RiskAssessmentResponse,
)

router = APIRouter(prefix="/assessments", tags=["assessments"])


@router.get("", response_model=RiskAssessmentCollectionResponse)
async def list_assessments(
    city_id: Optional[UUID] = Query(None, description="Filter by city ID"),
    indicator_id: Optional[UUID] = Query(None, description="Filter by indicator ID"),
    status: Optional[str] = Query(None, description="Filter by status (analyzed, partial, insufficient_data)"),
    severity: Optional[str] = Query(None, description="Filter by severity (low, moderate, high, critical)"),
    time_range: Tuple[Optional[datetime], Optional[datetime]] = Depends(validate_time_range),
    pagination: dict = Depends(pagination_params),
    repo: RiskAssessmentRepository = Depends(get_assessment_repo),
):
    """List risk assessments with optional filtering and pagination."""
    start_time, end_time = time_range

    items = await repo.search(
        city_id=city_id,
        indicator_id=indicator_id,
        status=status,
        severity=severity,
        start_time=start_time,
        end_time=end_time,
        offset=pagination["offset"],
        limit=pagination["limit"],
    )
    total = await repo.count_filtered(
        city_id=city_id,
        indicator_id=indicator_id,
        status=status,
        severity=severity,
        start_time=start_time,
        end_time=end_time,
    )
    total_pages = (total + pagination["limit_param"] - 1) // pagination["limit_param"]

    return RiskAssessmentCollectionResponse(
        data=[RiskAssessmentResponse.model_validate(item) for item in items],
        pagination={
            "page": pagination["page"],
            "limit": pagination["limit_param"],
            "total": total,
            "total_pages": total_pages,
        },
    )


@router.get("/{assessment_id}", response_model=RiskAssessmentDetailResponse)
async def get_assessment(
    assessment_id: UUID = Depends(validate_assessment_id),
    repo: RiskAssessmentRepository = Depends(get_assessment_repo),
):
    """Get a single risk assessment by ID."""
    assessment = await repo.get_by_id(assessment_id)
    if assessment is None:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=404,
            detail={"error": "not_found", "message": "Assessment not found"},
        )
    return RiskAssessmentDetailResponse(data=RiskAssessmentResponse.model_validate(assessment))