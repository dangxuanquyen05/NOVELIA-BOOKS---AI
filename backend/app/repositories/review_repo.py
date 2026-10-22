"""Repository for Book Reviews and customer rating aggregations."""

from typing import Dict, List, Optional, Tuple
from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from app.models.experience import Review
from app.models.user import User


class ReviewRepository:
    """Data access layer for Book Reviews and Star Ratings."""

    @staticmethod
    def get_by_book_id(
        db: Session, book_id: int, status: str = "APPROVED"
    ) -> List[Review]:
        return (
            db.query(Review)
            .options(selectinload(Review.user))
            .filter(Review.book_id == book_id, Review.status == status)
            .order_by(Review.created_at.desc())
            .all()
        )

    @staticmethod
    def get_user_review_for_book(
        db: Session, user_id: int, book_id: int
    ) -> Optional[Review]:
        return (
            db.query(Review)
            .options(selectinload(Review.user))
            .filter(Review.user_id == user_id, Review.book_id == book_id)
            .first()
        )

    @staticmethod
    def get_by_id(db: Session, review_id: int) -> Optional[Review]:
        return (
            db.query(Review)
            .options(selectinload(Review.user))
            .filter(Review.id == review_id)
            .first()
        )

    @staticmethod
    def create_review(
        db: Session,
        user_id: int,
        book_id: int,
        rating: int,
        title: Optional[str],
        comment: str,
        is_verified_purchase: bool = False,
    ) -> Review:
        review = Review(
            user_id=user_id,
            book_id=book_id,
            rating=rating,
            title=title,
            comment=comment,
            is_verified_purchase=is_verified_purchase,
            status="APPROVED",
        )
        db.add(review)
        db.commit()
        db.refresh(review)
        return review

    @staticmethod
    def update_review(
        db: Session,
        review: Review,
        rating: Optional[int] = None,
        title: Optional[str] = None,
        comment: Optional[str] = None,
    ) -> Review:
        if rating is not None:
            review.rating = rating
        if title is not None:
            review.title = title
        if comment is not None:
            review.comment = comment

        db.commit()
        db.refresh(review)
        return review

    @staticmethod
    def delete_review(db: Session, review: Review) -> None:
        db.delete(review)
        db.commit()

    @staticmethod
    def get_rating_summary(
        db: Session, book_id: int
    ) -> Tuple[float, int, Dict[str, int]]:
        """Compute average star rating, total review count, and star distribution."""
        reviews = (
            db.query(Review.rating)
            .filter(Review.book_id == book_id, Review.status == "APPROVED")
            .all()
        )

        total = len(reviews)
        distribution = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}

        if total == 0:
            return 0.0, 0, distribution

        total_stars = 0
        for (r,) in reviews:
            total_stars += r
            key = str(r)
            if key in distribution:
                distribution[key] += 1

        avg = round(total_stars / total, 1)
        return avg, total, distribution
