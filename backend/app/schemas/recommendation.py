"""Pydantic schemas for BookMatch AI personalized recommendations."""

from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class BookRecommendationItem(BaseModel):
    """Individual book recommendation item with score and grounded explanation."""

    book_id: int
    title: str
    slug: str
    price: Decimal = Field(..., description="Authoritative current price from MySQL")
    original_price: Optional[Decimal] = None
    primary_author: Optional[str] = None
    cover_image_url: Optional[str] = None
    category_id: Optional[int] = None
    category_name: Optional[str] = None
    available_stock: int = Field(..., ge=0, description="Real-time available stock (physical - reserved)")
    match_score: float = Field(..., ge=0.0, le=1.0, description="Normalized recommendation score 0.0 - 1.0")
    algorithm_type: str = Field(..., description="BOOKMATCH_AI, CONTENT_BASED, COLLABORATIVE, TRENDING")
    explanation: str = Field(..., description="Personalized explanation for why this book was chosen")
    explanation_source: str = Field("AI_GENERATED", description="AI_GENERATED or RULE_BASED_FALLBACK")


class UserTasteProfile(BaseModel):
    """Inferred reading taste profile of the authenticated user."""

    user_id: Optional[int] = None
    is_cold_start: bool = False
    top_categories: List[Dict[str, Any]] = Field(default_factory=list)
    top_authors: List[Dict[str, Any]] = Field(default_factory=list)
    total_orders_analyzed: int = 0
    total_reviews_analyzed: int = 0
    total_wishlist_analyzed: int = 0


class BookMatchResponse(BaseModel):
    """Complete response payload for BookMatch recommendation requests."""

    user_id: Optional[int] = None
    is_cold_start: bool = False
    algorithm: str = "BOOKMATCH_HYBRID"
    total_candidates_analyzed: int = 0
    recommendations: List[BookRecommendationItem] = Field(default_factory=list)
    taste_profile: Optional[UserTasteProfile] = None
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    disclaimer: str = (
        "Gợi ý dựa trên phân tích sở thích đọc thực tế và tồn kho sẵn có tại Novelia Books. "
        "Số liệu không cam kết mức độ cải thiện doanh số khi chưa qua đánh giá A/B test thực tế."
    )


class RecommendationEventCreate(BaseModel):
    """Telemetry event recording user interaction with recommended items."""

    book_id: int
    event_type: str = Field(..., description="VIEW, CLICK, ADD_TO_CART, DISMISS, PURCHASE")
    session_id: Optional[str] = None
    metadata_json: Optional[Dict[str, Any]] = None


class BaselineComparisonResponse(BaseModel):
    """Quality and metrics comparison between BookMatch AI and Popularity/Random baseline."""

    sample_size: int
    bookmatch_avg_affinity_score: float
    baseline_avg_affinity_score: float
    affinity_improvement_pct: float
    catalog_groundedness_rate: float = 1.0  # 100%
    in_stock_guarantee_rate: float = 1.0    # 100%
    evaluation_notes: str
