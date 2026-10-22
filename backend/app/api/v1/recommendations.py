"""FastAPI endpoints for BookMatch AI personalized book recommendations."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user_optional, get_db
from app.models.user import User
from app.schemas.recommendation import (
    BaselineComparisonResponse,
    BookMatchResponse,
    BookRecommendationItem,
    RecommendationEventCreate,
)
from app.services.bookmatch_service import BookMatchService

router = APIRouter(prefix="/recommendations", tags=["BookMatch AI Recommendations"])


@router.get(
    "/personalized",
    response_model=BookMatchResponse,
    status_code=status.HTTP_200_OK,
    summary="Lấy danh sách sách gợi ý cá nhân hóa từ BookMatch AI",
)
async def get_personalized_recommendations(
    limit: int = Query(6, ge=1, le=20, description="Số lượng sách cần gợi ý"),
    category_slug: Optional[str] = Query(None, description="Lọc theo slug danh mục"),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Generate personalized recommendations for authenticated user, or fallback cold-start for guests."""
    service = BookMatchService(db)
    return await service.get_recommendations(
        user=current_user,
        limit=limit,
        category_slug=category_slug,
    )


@router.get(
    "/baseline",
    response_model=List[BookRecommendationItem],
    status_code=status.HTTP_200_OK,
    summary="Lấy danh sách sách đề xuất theo mô hình baseline phổ thông",
)
def get_baseline_recommendations(
    limit: int = Query(6, ge=1, le=20, description="Số lượng sách cần lấy"),
    db: Session = Depends(get_db),
):
    """Retrieve popularity baseline recommendations (top sellers & top ratings) for evaluation."""
    service = BookMatchService(db)
    return service.get_baseline_recommendations(limit=limit)


@router.get(
    "/evaluation",
    response_model=BaselineComparisonResponse,
    status_code=status.HTTP_200_OK,
    summary="Đánh giá chất lượng BookMatch AI so với baseline",
)
async def evaluate_recommendations_against_baseline(
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Evaluate BookMatch AI precision, groundedness, and affinity improvement compared to baseline."""
    service = BookMatchService(db)
    return await service.evaluate_against_baseline(user=current_user)


@router.post(
    "/events",
    status_code=status.HTTP_201_CREATED,
    summary="Ghi nhận sự kiện tương tác của người dùng với sách (telemetry)",
)
def record_recommendation_event(
    payload: RecommendationEventCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """Record user behavioral events (VIEW, CLICK, ADD_TO_CART) to refine future recommendations."""
    service = BookMatchService(db)
    user_id = current_user.id if current_user else None
    event = service.record_interaction_event(
        user_id=user_id,
        session_id=payload.session_id,
        book_id=payload.book_id,
        event_type=payload.event_type,
        metadata_json=payload.metadata_json,
    )
    return {
        "success": True,
        "event_id": event.id,
        "event_type": event.event_type,
        "book_id": event.book_id,
    }
