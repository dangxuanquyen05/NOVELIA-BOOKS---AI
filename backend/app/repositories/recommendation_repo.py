"""Repository layer for BookMatch AI and personalized recommendation signals."""

from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Set, Tuple
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session, selectinload

from app.models.catalog import Author, Book, BookAuthor, BookCategory, Category
from app.models.commerce import Order, OrderItem, Wishlist, WishlistItem
from app.models.experience import Review
from app.models.inventory import Inventory
from app.models.user import UserPreference
from app.models.ai import BookRecommendation, UserBookEvent


class RecommendationRepository:
    """Encapsulates all database operations for user signals, candidate generation, and recommendations."""

    def __init__(self, db: Session):
        self.db = db

    def get_user_signals(self, user_id: int) -> Dict[str, Any]:
        """Collect permitted interaction signals for a user (orders, wishlist, reviews, preferences).

        Strict anti-IDOR: all queries strictly filter by user_id == user_id.
        """
        # 1. Past purchased books from completed or valid orders
        order_books_stmt = (
            select(OrderItem.book_id, func.count(OrderItem.id).label("freq"))
            .join(Order, OrderItem.order_id == Order.id)
            .where(Order.user_id == user_id, Order.status != "CANCELLED")
            .group_by(OrderItem.book_id)
        )
        order_results = self.db.execute(order_books_stmt).all()
        purchased_book_ids: Set[int] = {row[0] for row in order_results}

        # 2. Wishlist items
        wishlist_stmt = (
            select(WishlistItem.book_id)
            .join(Wishlist, WishlistItem.wishlist_id == Wishlist.id)
            .where(Wishlist.user_id == user_id)
        )
        wishlist_results = self.db.execute(wishlist_stmt).scalars().all()
        wishlist_book_ids: Set[int] = set(wishlist_results)

        # 3. High ratings & reviews (rating >= 4)
        review_stmt = (
            select(Review.book_id, Review.rating)
            .where(Review.user_id == user_id, Review.rating >= 4, Review.status == "APPROVED")
        )
        review_results = self.db.execute(review_stmt).all()
        reviewed_book_ids: Set[int] = {row[0] for row in review_results}

        # 4. Explicit user preferences
        pref_stmt = select(UserPreference).where(UserPreference.user_id == user_id)
        pref = self.db.execute(pref_stmt).scalar_one_or_none()

        # 5. Behavioral events from telemetry
        event_stmt = (
            select(UserBookEvent.book_id, UserBookEvent.event_type)
            .where(UserBookEvent.user_id == user_id)
            .order_by(desc(UserBookEvent.created_at))
            .limit(50)
        )
        event_results = self.db.execute(event_stmt).all()

        # Load all metadata for interacted books to compute category & author weights
        all_interacted_book_ids = purchased_book_ids | wishlist_book_ids | reviewed_book_ids | {r[0] for r in event_results}

        category_weights: Dict[int, float] = defaultdict(float)
        category_names: Dict[int, str] = {}
        author_weights: Dict[int, float] = defaultdict(float)
        author_names: Dict[int, str] = {}

        if all_interacted_book_ids:
            books_stmt = (
                select(Book)
                .options(
                    selectinload(Book.categories).selectinload(BookCategory.category),
                    selectinload(Book.authors).selectinload(BookAuthor.author),
                )
                .where(Book.id.in_(all_interacted_book_ids))
            )
            interacted_books = self.db.execute(books_stmt).scalars().all()

            for b in interacted_books:
                # Determine interaction weight multiplier
                multiplier = 1.0
                if b.id in purchased_book_ids:
                    multiplier += 3.0  # High signal
                if b.id in reviewed_book_ids:
                    multiplier += 2.5
                if b.id in wishlist_book_ids:
                    multiplier += 2.0

                for bc in b.categories:
                    cat_obj = getattr(bc, "category", None)
                    cid = getattr(bc, "category_id", None) or (getattr(cat_obj, "id", None) if cat_obj else None) or getattr(bc, "id", None)
                    cname = (getattr(cat_obj, "name", None) if cat_obj else None) or getattr(bc, "name", None)
                    if cid:
                        category_weights[cid] += multiplier
                        if cname:
                            category_names[cid] = cname

                for ba in b.authors:
                    auth_obj = getattr(ba, "author", None)
                    aid = getattr(ba, "author_id", None) or (getattr(auth_obj, "id", None) if auth_obj else None) or getattr(ba, "id", None)
                    aname = (getattr(auth_obj, "name", None) if auth_obj else None) or getattr(ba, "name", None)
                    if aid:
                        author_weights[aid] += multiplier
                        if aname:
                            author_names[aid] = aname

        # Incorporate explicit preferences if present
        if pref:
            if pref.preferred_categories and isinstance(pref.preferred_categories, list):
                for cat_item in pref.preferred_categories:
                    if isinstance(cat_item, int):
                        category_weights[cat_item] += 2.5
                    elif isinstance(cat_item, str):
                        # Find category by slug or name
                        cat_lookup = self.db.execute(
                            select(Category).where((Category.slug == cat_item) | (Category.name == cat_item))
                        ).scalar_one_or_none()
                        if cat_lookup:
                            category_weights[cat_lookup.id] += 2.5
                            category_names[cat_lookup.id] = cat_lookup.name
            if pref.preferred_authors and isinstance(pref.preferred_authors, list):
                for auth_item in pref.preferred_authors:
                    if isinstance(auth_item, int):
                        author_weights[auth_item] += 2.5
                    elif isinstance(auth_item, str):
                        auth_lookup = self.db.execute(
                            select(Author).where(Author.name.ilike(f"%{auth_item}%"))
                        ).scalars().first()
                        if auth_lookup:
                            author_weights[auth_lookup.id] += 2.5
                            author_names[auth_lookup.id] = auth_lookup.name

        # Format top categories and authors
        top_categories = [
            {"category_id": cid, "name": category_names.get(cid, f"Thể loại {cid}"), "weight": round(w, 2)}
            for cid, w in sorted(category_weights.items(), key=lambda x: x[1], reverse=True)[:5]
        ]
        top_authors = [
            {"author_id": aid, "name": author_names.get(aid, f"Tác giả {aid}"), "weight": round(w, 2)}
            for aid, w in sorted(author_weights.items(), key=lambda x: x[1], reverse=True)[:5]
        ]

        is_cold_start = (len(purchased_book_ids) == 0 and len(wishlist_book_ids) == 0 and len(reviewed_book_ids) == 0 and len(category_weights) == 0)

        return {
            "user_id": user_id,
            "is_cold_start": is_cold_start,
            "purchased_book_ids": purchased_book_ids,
            "category_weights": dict(category_weights),
            "author_weights": dict(author_weights),
            "top_categories": top_categories,
            "top_authors": top_authors,
            "total_orders_analyzed": len(purchased_book_ids),
            "total_reviews_analyzed": len(reviewed_book_ids),
            "total_wishlist_analyzed": len(wishlist_book_ids),
        }

    def get_candidate_books(
        self,
        exclude_book_ids: Optional[Set[int]] = None,
        category_slug: Optional[str] = None,
        limit: int = 50,
    ) -> List[Book]:
        """Fetch candidates strictly from real MySQL catalog with ACTIVE status and available stock.

        Ensures:
        1. Book.status == 'ACTIVE'
        2. Inventory.physical_stock > Inventory.reserved_stock (available_stock > 0)
        3. Excludes already purchased books if specified
        """
        stmt = (
            select(Book)
            .join(Inventory, Book.id == Inventory.book_id)
            .options(
                selectinload(Book.categories),
                selectinload(Book.authors),
                selectinload(Book.inventory),
                selectinload(Book.images),
            )
            .where(
                Book.status == "ACTIVE",
                (Inventory.physical_stock - Inventory.reserved_stock) > 0,
            )
        )

        if exclude_book_ids:
            stmt = stmt.where(~Book.id.in_(exclude_book_ids))

        if category_slug:
            stmt = stmt.join(BookCategory, Book.id == BookCategory.book_id).join(Category, BookCategory.category_id == Category.id).where(Category.slug == category_slug)

        # Ordering candidate search by newest and balanced availability
        stmt = stmt.order_by(desc(Book.created_at), Book.id.asc()).limit(limit)

        return list(self.db.execute(stmt).scalars().all())

    def get_popularity_baseline(self, limit: int = 6) -> List[Book]:
        """Retrieve authoritative active books with stock as baseline."""
        stmt = (
            select(Book)
            .join(Inventory, Book.id == Inventory.book_id)
            .options(
                selectinload(Book.categories),
                selectinload(Book.authors),
                selectinload(Book.inventory),
                selectinload(Book.images),
            )
            .where(
                Book.status == "ACTIVE",
                (Inventory.physical_stock - Inventory.reserved_stock) > 0,
            )
            .order_by(desc(Book.created_at), Book.id.asc())
            .limit(limit)
        )
        return list(self.db.execute(stmt).scalars().all())

    def record_user_event(
        self,
        user_id: Optional[int],
        session_id: Optional[str],
        book_id: int,
        event_type: str,
        metadata_json: Optional[Dict[str, Any]] = None,
    ) -> UserBookEvent:
        """Log behavioral interaction event into user_book_events."""
        event = UserBookEvent(
            user_id=user_id,
            session_id=session_id,
            book_id=book_id,
            event_type=event_type,
            metadata_json=metadata_json,
            created_at=datetime.now(timezone.utc),
        )
        self.db.add(event)
        self.db.commit()
        self.db.refresh(event)
        return event

    def persist_recommendations(
        self,
        user_id: int,
        recommendations: List[Dict[str, Any]],
        algorithm_type: str = "BOOKMATCH_AI",
    ) -> None:
        """Persist recommendation score and reason snapshots into book_recommendations table."""
        for item in recommendations:
            book_id = item["book_id"]
            score = Decimal(str(round(item["match_score"], 4)))
            reason = item.get("explanation", "")[:250]

            # Check if record exists
            existing = self.db.execute(
                select(BookRecommendation).where(
                    BookRecommendation.user_id == user_id,
                    BookRecommendation.book_id == book_id,
                    BookRecommendation.algorithm_type == algorithm_type,
                )
            ).scalar_one_or_none()

            if existing:
                existing.score = score
                existing.reason = reason
                existing.generated_at = datetime.now(timezone.utc)
            else:
                rec = BookRecommendation(
                    user_id=user_id,
                    book_id=book_id,
                    algorithm_type=algorithm_type,
                    score=score,
                    reason=reason,
                    generated_at=datetime.now(timezone.utc),
                )
                self.db.add(rec)

        self.db.commit()
