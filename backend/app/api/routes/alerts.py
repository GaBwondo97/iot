"""
Alert API routes.
"""

from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import (
    get_alert_repo,
    pagination_params,
    validate_alert_id,
)
from app.repositories import AlertRepository
from app.schemas import AlertCollectionResponse, AlertDetailResponse, AlertResponse

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=AlertCollectionResponse)
async def list_alerts(
    city_id: Optional[UUID] = Query(None, description="Filter by city ID"),
    severity: Optional[str] = Query(None, description="Filter by severity (low, moderate, high, critical)"),
    status: Optional[str] = Query(None, description="Filter by status (active, acknowledged, resolved)"),
    pagination: dict = Depends(pagination_params),
    repo: AlertRepository = Depends(get_alert_repo),
):
    """List alerts with optional filtering and pagination."""
    items = await repo.search(
        city_id=city_id,
        severity=severity,
        status=status,
        offset=pagination["offset"],
        limit=pagination["limit"],
    )
    total = await repo.count_filtered(city_id=city_id, severity=severity, status=status)
    total_pages = (total + pagination["limit_param"] - 1) // pagination["limit_param"]

    return AlertCollectionResponse(
        data=[AlertResponse.model_validate(item) for item in items],
        pagination={
            "page": pagination["page"],
            "limit": pagination["limit_param"],
            "total": total,
            "total_pages": total_pages,
        },
    )


@router.get("/{alert_id}", response_model=AlertDetailResponse)
async def get_alert(
    alert_id: UUID = Depends(validate_alert_id),
    repo: AlertRepository = Depends(get_alert_repo),
):
    """Get a single alert by ID."""
    alert = await repo.get_by_id(alert_id)
    if alert is None:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=404,
            detail={"error": "not_found", "message": "Alert not found"},
        )
    return AlertDetailResponse(data=AlertResponse.model_validate(alert))