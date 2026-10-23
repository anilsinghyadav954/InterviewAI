import logging
from fastapi import APIRouter, Depends, Query, status
from typing import List, Optional

logger = logging.getLogger(__name__)

from app.routes.auth import get_current_user
from app.schemas.performance import (
    PerformanceOverviewResponse,
    PerformanceTrendPoint,
    SkillPerformanceItem,
    CategoryPerformanceItem,
    RolePerformanceItem,
    InterviewTypePerformanceItem,
    PerformanceInsightsResponse,
    RecentActivityItem,
)
from app.services.performance_service import (
    get_performance_overview,
    get_performance_trend,
    get_skill_performance,
    get_category_performance,
    get_role_performance,
    get_interview_type_performance,
    get_performance_insights,
    get_recent_activity,
)

router = APIRouter(prefix="/api/performance", tags=["Performance Analytics & Reports"])


@router.get(
    "/overview",
    response_model=PerformanceOverviewResponse,
    status_code=status.HTTP_200_OK,
    summary="Get candidate overall performance summary metrics",
)
def get_overview(
    time_range: Optional[str] = Query(None, description="7d, 30d, 90d, or all"),
    interview_type: Optional[str] = Query(None, description="All, Technical, HR, Mixed"),
    target_role: Optional[str] = Query(None, description="Specific target role filter"),
    current_user: dict = Depends(get_current_user),
):
    return get_performance_overview(
        user_id=current_user["id"],
        time_range=time_range,
        interview_type=interview_type,
        target_role=target_role,
    )


@router.get(
    "/trend",
    response_model=List[PerformanceTrendPoint],
    status_code=status.HTTP_200_OK,
    summary="Get chronological interview score history for trend charting",
)
def get_trend(
    time_range: Optional[str] = Query(None, description="7d, 30d, 90d, or all"),
    interview_type: Optional[str] = Query(None, description="All, Technical, HR, Mixed"),
    target_role: Optional[str] = Query(None, description="Specific target role filter"),
    current_user: dict = Depends(get_current_user),
):
    return get_performance_trend(
        user_id=current_user["id"],
        time_range=time_range,
        interview_type=interview_type,
        target_role=target_role,
    )


@router.get(
    "/skills",
    response_model=List[SkillPerformanceItem],
    status_code=status.HTTP_200_OK,
    summary="Get skill/topic competency breakdown from evaluated questions",
)
def get_skills(
    time_range: Optional[str] = Query(None, description="7d, 30d, 90d, or all"),
    interview_type: Optional[str] = Query(None, description="All, Technical, HR, Mixed"),
    target_role: Optional[str] = Query(None, description="Specific target role filter"),
    current_user: dict = Depends(get_current_user),
):
    return get_skill_performance(
        user_id=current_user["id"],
        time_range=time_range,
        interview_type=interview_type,
        target_role=target_role,
    )


@router.get(
    "/categories",
    response_model=List[CategoryPerformanceItem],
    status_code=status.HTTP_200_OK,
    summary="Get performance aggregated by question category",
)
def get_categories(
    time_range: Optional[str] = Query(None, description="7d, 30d, 90d, or all"),
    interview_type: Optional[str] = Query(None, description="All, Technical, HR, Mixed"),
    target_role: Optional[str] = Query(None, description="Specific target role filter"),
    current_user: dict = Depends(get_current_user),
):
    return get_category_performance(
        user_id=current_user["id"],
        time_range=time_range,
        interview_type=interview_type,
        target_role=target_role,
    )


@router.get(
    "/roles",
    response_model=List[RolePerformanceItem],
    status_code=status.HTTP_200_OK,
    summary="Get performance aggregated across practiced target roles",
)
def get_roles(
    time_range: Optional[str] = Query(None, description="7d, 30d, 90d, or all"),
    interview_type: Optional[str] = Query(None, description="All, Technical, HR, Mixed"),
    current_user: dict = Depends(get_current_user),
):
    return get_role_performance(
        user_id=current_user["id"],
        time_range=time_range,
        interview_type=interview_type,
    )


@router.get(
    "/types",
    response_model=List[InterviewTypePerformanceItem],
    status_code=status.HTTP_200_OK,
    summary="Get performance breakdown by interview type (Technical, HR, Mixed)",
)
def get_types(
    time_range: Optional[str] = Query(None, description="7d, 30d, 90d, or all"),
    target_role: Optional[str] = Query(None, description="Specific target role filter"),
    current_user: dict = Depends(get_current_user),
):
    return get_interview_type_performance(
        user_id=current_user["id"],
        time_range=time_range,
        target_role=target_role,
    )


@router.get(
    "/insights",
    response_model=PerformanceInsightsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get strengths, weaknesses, and actionable improvement recommendations",
)
def get_insights(
    time_range: Optional[str] = Query(None, description="7d, 30d, 90d, or all"),
    interview_type: Optional[str] = Query(None, description="All, Technical, HR, Mixed"),
    target_role: Optional[str] = Query(None, description="Specific target role filter"),
    current_user: dict = Depends(get_current_user),
):
    return get_performance_insights(
        user_id=current_user["id"],
        time_range=time_range,
        interview_type=interview_type,
        target_role=target_role,
    )


@router.get(
    "/recent-activity",
    response_model=List[RecentActivityItem],
    status_code=status.HTTP_200_OK,
    summary="Get recent candidate actions (resumes, question banks, mock sessions)",
)
def get_activity(
    limit: int = Query(6, ge=1, le=20),
    current_user: dict = Depends(get_current_user),
):
    return get_recent_activity(user_id=current_user["id"], limit=limit)
