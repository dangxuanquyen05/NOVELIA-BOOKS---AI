"""Database repository for Book Catalog, Categories, Authors, Publishers, and Associations."""

import re
from typing import List, Optional, Tuple
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, selectinload

from app.models.catalog import Author, Book, BookAuthor, BookCategory, BookImage, Category, Publisher
from app.models.inventory import Inventory, InventoryTransaction
from app.schemas.catalog import (
    AuthorCreate,
    AuthorUpdate,
    BookCreate,
    BookFilterParams,
    BookUpdate,
    CategoryCreate,
    CategoryUpdate,
    PublisherCreate,
    PublisherUpdate,
)


def generate_slug(text: str) -> str:
    """Generate a clean URL slug from text."""
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_-]+", "-", text)
    return text.strip("-")


# ============================================================================
# CATEGORY REPOSITORY
# ============================================================================


class CategoryRepository:
    """Data access layer for Categories."""

    @staticmethod
    def get_by_id(db: Session, category_id: int) -> Optional[Category]:
        return db.query(Category).filter(Category.id == category_id).first()

    @staticmethod
    def get_by_slug(db: Session, slug: str) -> Optional[Category]:
        return db.query(Category).filter(Category.slug == slug).first()

    @staticmethod
    def get_all(db: Session, parent_only: bool = False) -> List[Category]:
        query = db.query(Category)
        if parent_only:
            query = query.filter(Category.parent_id.is_(None))
        return query.order_by(Category.display_order.asc(), Category.name.asc()).all()

    @staticmethod
    def get_tree(db: Session) -> List[Category]:
        """Fetch all root categories with their subcategories preloaded."""
        return (
            db.query(Category)
            .filter(Category.parent_id.is_(None))
            .options(selectinload(Category.subcategories))
            .order_by(Category.display_order.asc(), Category.name.asc())
            .all()
        )

    @staticmethod
    def count_books_in_category(db: Session, category_id: int) -> int:
        return (
            db.query(func.count(BookCategory.id))
            .filter(BookCategory.category_id == category_id)
            .scalar()
            or 0
        )

    @staticmethod
    def create(db: Session, data: CategoryCreate) -> Category:
        slug = data.slug or generate_slug(data.name)
        category = Category(
            name=data.name,
            slug=slug,
            description=data.description,
            parent_id=data.parent_id,
            display_order=data.display_order,
        )
        db.add(category)
        db.commit()
        db.refresh(category)
        return category

    @staticmethod
    def update(db: Session, category: Category, data: CategoryUpdate) -> Category:
        update_data = data.model_dump(exclude_unset=True)
        if "name" in update_data and not update_data.get("slug"):
            update_data["slug"] = generate_slug(update_data["name"])

        for field, value in update_data.items():
            setattr(category, field, value)

        db.commit()
        db.refresh(category)
        return category

    @staticmethod
    def delete(db: Session, category: Category) -> None:
        db.delete(category)
        db.commit()


# ============================================================================
# AUTHOR REPOSITORY
# ============================================================================


class AuthorRepository:
    """Data access layer for Authors."""

    @staticmethod
    def get_by_id(db: Session, author_id: int) -> Optional[Author]:
        return db.query(Author).filter(Author.id == author_id).first()

    @staticmethod
    def get_by_slug(db: Session, slug: str) -> Optional[Author]:
        return db.query(Author).filter(Author.slug == slug).first()

    @staticmethod
    def get_all(
        db: Session, skip: int = 0, limit: int = 100, query: Optional[str] = None
    ) -> List[Author]:
        q = db.query(Author)
        if query:
            q = q.filter(Author.name.ilike(f"%{query}%"))
        return q.order_by(Author.name.asc()).offset(skip).limit(limit).all()

    @staticmethod
    def create(db: Session, data: AuthorCreate) -> Author:
        slug = data.slug or generate_slug(data.name)
        author = Author(
            name=data.name,
            slug=slug,
            bio=data.bio,
            avatar_url=data.avatar_url,
            birth_year=data.birth_year,
            nationality=data.nationality,
        )
        db.add(author)
        db.commit()
        db.refresh(author)
        return author

    @staticmethod
    def update(db: Session, author: Author, data: AuthorUpdate) -> Author:
        update_data = data.model_dump(exclude_unset=True)
        if "name" in update_data and not update_data.get("slug"):
            update_data["slug"] = generate_slug(update_data["name"])

        for field, value in update_data.items():
            setattr(author, field, value)

        db.commit()
        db.refresh(author)
        return author

    @staticmethod
    def delete(db: Session, author: Author) -> None:
        db.delete(author)
        db.commit()


# ============================================================================
# PUBLISHER REPOSITORY
# ============================================================================


class PublisherRepository:
    """Data access layer for Publishers."""

    @staticmethod
    def get_by_id(db: Session, publisher_id: int) -> Optional[Publisher]:
        return db.query(Publisher).filter(Publisher.id == publisher_id).first()

    @staticmethod
    def get_by_slug(db: Session, slug: str) -> Optional[Publisher]:
        return db.query(Publisher).filter(Publisher.slug == slug).first()

    @staticmethod
    def get_all(db: Session, skip: int = 0, limit: int = 100) -> List[Publisher]:
        return db.query(Publisher).order_by(Publisher.name.asc()).offset(skip).limit(limit).all()

    @staticmethod
    def create(db: Session, data: PublisherCreate) -> Publisher:
        slug = data.slug or generate_slug(data.name)
        publisher = Publisher(
            name=data.name,
            slug=slug,
            contact_info=data.contact_info,
            address=data.address,
            website=data.website,
        )
        db.add(publisher)
        db.commit()
        db.refresh(publisher)
        return publisher

    @staticmethod
    def update(db: Session, publisher: Publisher, data: PublisherUpdate) -> Publisher:
        update_data = data.model_dump(exclude_unset=True)
        if "name" in update_data and not update_data.get("slug"):
            update_data["slug"] = generate_slug(update_data["name"])

        for field, value in update_data.items():
            setattr(publisher, field, value)

        db.commit()
        db.refresh(publisher)
        return publisher

    @staticmethod
    def delete(db: Session, publisher: Publisher) -> None:
        db.delete(publisher)
        db.commit()


# ============================================================================
# BOOK REPOSITORY
# ============================================================================


class BookRepository:
    """Data access layer for Books with optimized eager loading and multi-criteria filters."""

    @staticmethod
    def _eager_load_options():
        """Standard relationships required for book rendering."""
        return [
            selectinload(Book.publisher),
            selectinload(Book.authors).selectinload(BookAuthor.author),
            selectinload(Book.categories).selectinload(BookCategory.category),
            selectinload(Book.images),
            selectinload(Book.inventory),
        ]

    @classmethod
    def get_by_id(cls, db: Session, book_id: int) -> Optional[Book]:
        return (
            db.query(Book)
            .options(*cls._eager_load_options())
            .filter(Book.id == book_id)
            .first()
        )

    @classmethod
    def get_by_slug(cls, db: Session, slug: str) -> Optional[Book]:
        return (
            db.query(Book)
            .options(*cls._eager_load_options())
            .filter(Book.slug == slug)
            .first()
        )

    @classmethod
    def get_by_isbn(cls, db: Session, isbn: str) -> Optional[Book]:
        return db.query(Book).filter(Book.isbn == isbn).first()

    @classmethod
    def get_by_sku(cls, db: Session, sku: str) -> Optional[Book]:
        return db.query(Book).filter(Book.sku == sku).first()

    @classmethod
    def list_books(
        cls, db: Session, params: BookFilterParams
    ) -> Tuple[List[Book], int]:
        """Query books with search, categorization, price range, cover type, sort, and pagination."""
        query = db.query(Book).options(*cls._eager_load_options())

        # Status filter
        if params.status and params.status != "ALL":
            query = query.filter(Book.status == params.status)

        # Keyword search (Title, ISBN, or Author Name)
        if params.query:
            term = f"%{params.query.strip()}%"
            query = query.filter(
                or_(
                    Book.title.ilike(term),
                    Book.isbn.ilike(term),
                    Book.authors.any(
                        BookAuthor.author.has(Author.name.ilike(term))
                    ),
                )
            )

        # Category filter (by slug or ID)
        if params.category_slug:
            query = query.filter(
                Book.categories.any(
                    BookCategory.category.has(Category.slug == params.category_slug)
                )
            )
        elif params.category_id:
            query = query.filter(
                Book.categories.any(BookCategory.category_id == params.category_id)
            )

        # Author filter
        if params.author_id:
            query = query.filter(
                Book.authors.any(BookAuthor.author_id == params.author_id)
            )

        # Publisher filter
        if params.publisher_id:
            query = query.filter(Book.publisher_id == params.publisher_id)

        # Price range
        if params.min_price is not None:
            query = query.filter(Book.price >= params.min_price)
        if params.max_price is not None:
            query = query.filter(Book.price <= params.max_price)

        # Cover type
        if params.cover_type:
            query = query.filter(Book.cover_type == params.cover_type)

        # Count total matching records before pagination
        total = query.count()

        # Sorting logic
        if params.sort_by == "price_asc":
            query = query.order_by(Book.price.asc())
        elif params.sort_by == "price_desc":
            query = query.order_by(Book.price.desc())
        elif params.sort_by == "title_asc":
            query = query.order_by(Book.title.asc())
        elif params.sort_by == "title_desc":
            query = query.order_by(Book.title.desc())
        elif params.sort_by == "discount_desc":
            query = query.order_by((Book.original_price - Book.price).desc())
        else:  # newest / default
            query = query.order_by(Book.created_at.desc())

        # Pagination
        offset = (params.page - 1) * params.page_size
        items = query.offset(offset).limit(params.page_size).all()

        return items, total

    @classmethod
    def get_featured_books(cls, db: Session, limit: int = 8) -> List[Book]:
        """Fetch featured books (active books ordered by discount or newest)."""
        return (
            db.query(Book)
            .options(*cls._eager_load_options())
            .filter(Book.status == "ACTIVE")
            .order_by((Book.original_price - Book.price).desc(), Book.created_at.desc())
            .limit(limit)
            .all()
        )

    @classmethod
    def get_related_books(
        cls, db: Session, book_id: int, limit: int = 4
    ) -> List[Book]:
        """Find related books sharing categories or authors, excluding the reference book."""
        target_book = db.query(Book).filter(Book.id == book_id).first()
        if not target_book:
            return []

        category_ids = [bc.category_id for bc in target_book.categories]
        author_ids = [ba.author_id for ba in target_book.authors]

        related_query = (
            db.query(Book)
            .options(*cls._eager_load_options())
            .filter(
                Book.id != book_id,
                Book.status == "ACTIVE",
                or_(
                    Book.categories.any(BookCategory.category_id.in_(category_ids))
                    if category_ids
                    else False,
                    Book.authors.any(BookAuthor.author_id.in_(author_ids))
                    if author_ids
                    else False,
                ),
            )
            .order_by(Book.created_at.desc())
            .limit(limit)
        )
        return related_query.all()

    @classmethod
    def create_book(cls, db: Session, data: BookCreate) -> Book:
        """Create a complete book publication with inventory, authors, categories, and images."""
        slug = data.slug or generate_slug(data.title)

        book = Book(
            isbn=data.isbn,
            sku=data.sku,
            title=data.title,
            slug=slug,
            publisher_id=data.publisher_id,
            price=data.price,
            original_price=data.original_price,
            page_count=data.page_count,
            dimension=data.dimension,
            weight_grams=data.weight_grams,
            cover_type=data.cover_type,
            description=data.description,
            sample_text=data.sample_text,
            cover_image_url=data.cover_image_url,
            status=data.status,
            published_date=data.published_date,
        )
        db.add(book)
        db.flush()

        # Attach Authors
        primary_id = data.primary_author_id or (data.author_ids[0] if data.author_ids else None)
        for idx, auth_id in enumerate(data.author_ids):
            assoc = BookAuthor(
                book_id=book.id,
                author_id=auth_id,
                is_primary=(auth_id == primary_id),
                order_index=idx,
            )
            db.add(assoc)

        # Attach Categories
        for cat_id in data.category_ids:
            cat_assoc = BookCategory(book_id=book.id, category_id=cat_id)
            db.add(cat_assoc)

        # Attach Images
        if data.images:
            for img in data.images:
                book_img = BookImage(
                    book_id=book.id,
                    image_url=img.image_url,
                    alt_text=img.alt_text,
                    display_order=img.display_order,
                    is_cover=img.is_cover,
                )
                db.add(book_img)

        # Initialize Inventory
        inventory = Inventory(
            book_id=book.id,
            physical_stock=data.initial_stock,
            reserved_stock=0,
            low_stock_threshold=10,
        )
        db.add(inventory)
        db.flush()

        # Record Initial Inventory Transaction
        if data.initial_stock > 0:
            tx = InventoryTransaction(
                inventory_id=inventory.id,
                transaction_type="IMPORT",
                quantity_change=data.initial_stock,
                balance_after=data.initial_stock,
                reference_code=f"INIT-{book.sku}",
                reason="Initial inventory creation for book catalog",
            )
            db.add(tx)

        db.commit()
        return cls.get_by_id(db, book.id)

    @classmethod
    def update_book(cls, db: Session, book: Book, data: BookUpdate) -> Book:
        """Update existing book record and synchronize authors/categories if provided."""
        update_dict = data.model_dump(
            exclude_unset=True, exclude={"author_ids", "category_ids"}
        )

        if "title" in update_dict and not update_dict.get("slug"):
            update_dict["slug"] = generate_slug(update_dict["title"])

        for field, value in update_dict.items():
            setattr(book, field, value)

        # Synchronize Authors if provided
        if data.author_ids is not None:
            db.query(BookAuthor).filter(BookAuthor.book_id == book.id).delete()
            for idx, auth_id in enumerate(data.author_ids):
                db.add(
                    BookAuthor(
                        book_id=book.id,
                        author_id=auth_id,
                        is_primary=(idx == 0),
                        order_index=idx,
                    )
                )

        # Synchronize Categories if provided
        if data.category_ids is not None:
            db.query(BookCategory).filter(BookCategory.book_id == book.id).delete()
            for cat_id in data.category_ids:
                db.add(BookCategory(book_id=book.id, category_id=cat_id))

        db.commit()
        return cls.get_by_id(db, book.id)

    @staticmethod
    def delete_book(db: Session, book: Book) -> None:
        """Permanently delete book or mark as DISCONTINUED."""
        db.delete(book)
        db.commit()
