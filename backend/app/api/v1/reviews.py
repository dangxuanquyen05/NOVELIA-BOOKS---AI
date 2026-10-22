"""Book reviews and star ratings API endpoints."""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.database.connection import get_db
from app.models.user import User
from app.schemas.auth import MessageResponse
from app.schemas.experience import (
    BookReviewSummary,
    ReviewCreateRequest,
    ReviewRead,
    ReviewUpdateRequest,
)
from app.services.review_service import ReviewService

router = APIRouter(tags=["Book Reviews & Customer Ratings"])


@router.get(
    "/catalog/books/{book_id}/reviews",
    response_model=BookReviewSummary,
    summary="Get public reviews, star distribution, and average rating for a book",
)
def get_book_reviews(
    book_id: int,
    db: Session = Depends(get_db),
):
    return ReviewService.get_book_reviews(db, book_id=book_id)


@router.post(
    "/catalog/books/{book_id}/reviews",
    response_model=ReviewRead,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a verified book review with star rating (Customer)",
)
def create_book_review(
    book_id: int,
    data: ReviewCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return ReviewService.create_review(
        db,
        user=current_user,
        book_id=book_id,
        data=data,
    )


@router.put(
    "/catalog/reviews/{review_id}",
    response_model=ReviewRead,
    summary="Update an existing review by the author",
)
def update_book_review(
    review_id: int,
    data: ReviewUpdateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    return ReviewService.update_review(
        db,
        user=current_user,
        review_id=review_id,
        data=data,
    )


@router.delete(
    "/catalog/reviews/{review_id}",
    response_model=MessageResponse,
    summary="Delete a review (Author or Admin)",
)
def delete_book_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    ReviewService.delete_review(db, user=current_user, review_id=review_id)
    return MessageResponse(message="Đã xóa đánh giá thành công.")
