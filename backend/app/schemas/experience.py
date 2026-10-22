"""Pydantic schemas for Book Reviews, star ratings, and review summaries."""

from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ReviewCreateRequest(BaseModel):
    rating: int = Field(..., ge=1, le=5, description="Star rating from 1 to 5")
    title: Optional[str] = Field(None, max_length=150, description="Short summary title")
    comment: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="Detailed review content (min 10 characters to prevent spam)",
    )


class ReviewUpdateRequest(BaseModel):
    rating: Optional[int] = Field(None, ge=1, le=5)
    title: Optional[str] = Field(None, max_length=150)
    comment: Optional[str] = Field(None, min_length=10, max_length=2000)


class ReviewRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    book_id: int
    user_id: int
    user_name: str
    rating: int
    title: Optional[str] = None
    comment: str
    is_verified_purchase: bool
    status: str
    created_at: datetime
    updated_at: datetime


class BookReviewSummary(BaseModel):
    average_rating: float = 0.0
    total_reviews: int = 0
    rating_distribution: Dict[str, int] = Field(
        default_factory=lambda: {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}
    )
    reviews: List[ReviewRead] = []
