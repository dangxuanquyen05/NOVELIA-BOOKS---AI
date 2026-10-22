"""Service layer for customer reviews, star ratings, and community validations."""

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.catalog import Book
from app.models.commerce import Order, OrderItem
from app.models.experience import Review
from app.models.user import User
from app.repositories.review_repo import ReviewRepository
from app.repositories.user_repo import UserRepository
from app.schemas.experience import (
    BookReviewSummary,
    ReviewCreateRequest,
    ReviewRead,
    ReviewUpdateRequest,
)


def to_review_read(r: Review) -> ReviewRead:
    user_name = r.user.full_name if r.user else "Độc giả ẩn danh"
    return ReviewRead(
        id=r.id,
        book_id=r.book_id,
        user_id=r.user_id,
        user_name=user_name,
        rating=r.rating,
        title=r.title,
        comment=r.comment,
        is_verified_purchase=r.is_verified_purchase,
        status=r.status,
        created_at=r.created_at,
        updated_at=r.updated_at,
    )


class ReviewService:
    """Domain logic for book reviews and anti-spam controls."""

    @classmethod
    def get_book_reviews(cls, db: Session, book_id: int) -> BookReviewSummary:
        book = db.query(Book).filter(Book.id == book_id).first()
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sách ID {book_id} không tồn tại.",
            )

        reviews = ReviewRepository.get_by_book_id(db, book_id)
        avg, total, dist = ReviewRepository.get_rating_summary(db, book_id)

        return BookReviewSummary(
            average_rating=avg,
            total_reviews=total,
            rating_distribution=dist,
            reviews=[to_review_read(r) for r in reviews],
        )

    @classmethod
    def create_review(
        cls, db: Session, user: User, book_id: int, data: ReviewCreateRequest
    ) -> ReviewRead:
        book = db.query(Book).filter(Book.id == book_id).first()
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sách ID {book_id} không tồn tại.",
            )

        # Anti-duplicate rule
        existing = ReviewRepository.get_user_review_for_book(db, user.id, book_id)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Bạn đã viết đánh giá cho cuốn sách này rồi. Vui lòng chỉnh sửa đánh giá hiện tại thay vì tạo mới.",
            )

        # Check verified purchase
        is_verified = (
            db.query(OrderItem)
            .join(Order)
            .filter(
                Order.user_id == user.id,
                OrderItem.book_id == book_id,
                Order.status.in_(["COMPLETED", "DELIVERED"]),
            )
            .first()
            is not None
        )

        review = ReviewRepository.create_review(
            db=db,
            user_id=user.id,
            book_id=book_id,
            rating=data.rating,
            title=data.title,
            comment=data.comment,
            is_verified_purchase=is_verified,
        )
        return to_review_read(review)

    @classmethod
    def update_review(
        cls, db: Session, user: User, review_id: int, data: ReviewUpdateRequest
    ) -> ReviewRead:
        review = ReviewRepository.get_by_id(db, review_id)
        if not review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Đánh giá không tồn tại.",
            )

        if review.user_id != user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bạn không có quyền chỉnh sửa bài đánh giá của người khác.",
            )

        updated = ReviewRepository.update_review(
            db=db,
            review=review,
            rating=data.rating,
            title=data.title,
            comment=data.comment,
        )
        return to_review_read(updated)

    @classmethod
    def delete_review(cls, db: Session, user: User, review_id: int) -> None:
        review = ReviewRepository.get_by_id(db, review_id)
        if not review:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Đánh giá không tồn tại.",
            )

        user_roles = UserRepository.get_user_role_names(user)
        is_admin = "ADMIN" in user_roles

        if review.user_id != user.id and not is_admin:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Bạn không có quyền xóa đánh giá này.",
            )

        ReviewRepository.delete_review(db, review)
