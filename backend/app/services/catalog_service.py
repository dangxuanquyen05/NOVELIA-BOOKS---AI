"""Catalog service coordinating business rules, conversions, and validations."""

import math
from typing import List, Optional, Union
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.catalog import Book, Category
from app.repositories.catalog_repo import (
    AuthorRepository,
    BookRepository,
    CategoryRepository,
    PublisherRepository,
)
from app.schemas.catalog import (
    AuthorCreate,
    AuthorRead,
    AuthorUpdate,
    BookAuthorRead,
    BookCategoryRead,
    BookCreate,
    BookDetailRead,
    BookFilterParams,
    BookImageRead,
    BookListRead,
    BookUpdate,
    CategoryCreate,
    CategoryRead,
    CategoryTreeRead,
    CategoryUpdate,
    PaginatedBooksResponse,
    PublisherCreate,
    PublisherRead,
    PublisherUpdate,
)


def to_book_list_read(book: Book) -> BookListRead:
    """Transform an ORM Book model into a clean BookListRead schema."""
    # Calculate discount percent
    discount = 0
    if book.original_price and book.original_price > book.price:
        discount = int(
            round(((float(book.original_price) - float(book.price)) / float(book.original_price)) * 100)
        )

    # Format authors
    authors_read: List[BookAuthorRead] = []
    primary_author_name: Optional[str] = None
    sorted_authors = sorted(book.authors or [], key=lambda ba: ba.order_index)
    for ba in sorted_authors:
        if ba.author:
            authors_read.append(
                BookAuthorRead(
                    author_id=ba.author.id,
                    name=ba.author.name,
                    slug=ba.author.slug,
                    is_primary=ba.is_primary,
                    order_index=ba.order_index,
                )
            )
            if ba.is_primary or primary_author_name is None:
                primary_author_name = ba.author.name

    # Format categories
    categories_read: List[BookCategoryRead] = []
    for bc in book.categories or []:
        if bc.category:
            categories_read.append(
                BookCategoryRead(
                    category_id=bc.category.id,
                    name=bc.category.name,
                    slug=bc.category.slug,
                )
            )

    # Stock available
    available = book.inventory.available_stock if book.inventory else 0
    in_stock = available > 0 and book.status != "OUT_OF_STOCK"

    return BookListRead(
        id=book.id,
        isbn=book.isbn,
        sku=book.sku,
        title=book.title,
        slug=book.slug,
        price=book.price,
        original_price=book.original_price,
        discount_percent=discount,
        cover_image_url=book.cover_image_url,
        cover_type=book.cover_type,
        status=book.status,
        primary_author=primary_author_name,
        authors=authors_read,
        categories=categories_read,
        stock_available=available,
        is_in_stock=in_stock,
        created_at=book.created_at,
    )


def to_book_detail_read(book: Book) -> BookDetailRead:
    """Transform an ORM Book model into a complete BookDetailRead schema."""
    list_dto = to_book_list_read(book)

    publisher_dto = None
    if book.publisher:
        publisher_dto = PublisherRead.model_validate(book.publisher)

    images_dto = [
        BookImageRead(
            id=img.id,
            image_url=img.image_url,
            alt_text=img.alt_text,
            display_order=img.display_order,
            is_cover=img.is_cover,
        )
        for img in sorted(book.images or [], key=lambda i: i.display_order)
    ]

    return BookDetailRead(
        **list_dto.model_dump(),
        publisher=publisher_dto,
        page_count=book.page_count,
        dimension=book.dimension,
        weight_grams=book.weight_grams,
        description=book.description,
        sample_text=book.sample_text,
        published_date=book.published_date,
        images=images_dto,
        updated_at=book.updated_at,
    )


class CatalogService:
    """Core domain business logic for catalog queries, CRUD, and validations."""

    # ========================================================================
    # BOOK OPERATIONS
    # ========================================================================

    @classmethod
    def get_books(cls, db: Session, params: BookFilterParams) -> PaginatedBooksResponse:
        """Fetch paginated books with multi-criteria filters."""
        items, total = BookRepository.list_books(db, params)
        total_pages = math.ceil(total / params.page_size) if total > 0 else 0

        read_items = [to_book_list_read(book) for book in items]
        return PaginatedBooksResponse(
            items=read_items,
            total=total,
            page=params.page,
            page_size=params.page_size,
            total_pages=total_pages,
        )

    @classmethod
    def get_book_by_slug_or_id(cls, db: Session, identifier: str) -> BookDetailRead:
        """Fetch book details by either numeric ID or URL slug."""
        book: Optional[Book] = None
        if identifier.isdigit():
            book = BookRepository.get_by_id(db, int(identifier))

        if not book:
            book = BookRepository.get_by_slug(db, identifier)

        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Sách với mã hoặc đường dẫn '{identifier}' không tồn tại trong hệ thống.",
            )

        return to_book_detail_read(book)

    @classmethod
    def get_featured_books(cls, db: Session, limit: int = 8) -> List[BookListRead]:
        """Fetch featured books for storefront showcase."""
        books = BookRepository.get_featured_books(db, limit=limit)
        return [to_book_list_read(b) for b in books]

    @classmethod
    def get_related_books(
        cls, db: Session, book_id: int, limit: int = 4
    ) -> List[BookListRead]:
        """Fetch related recommendations for a specific book."""
        books = BookRepository.get_related_books(db, book_id=book_id, limit=limit)
        return [to_book_list_read(b) for b in books]

    @classmethod
    def create_book(cls, db: Session, data: BookCreate) -> BookDetailRead:
        """Validate and create a new book publication."""
        # 1. Verify Publisher exists
        if not PublisherRepository.get_by_id(db, data.publisher_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Nhà xuất bản ID {data.publisher_id} không tồn tại.",
            )

        # 2. Verify Authors exist
        for auth_id in data.author_ids:
            if not AuthorRepository.get_by_id(db, auth_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Tác giả ID {auth_id} không tồn tại.",
                )

        # 3. Verify Categories exist
        for cat_id in data.category_ids:
            if not CategoryRepository.get_by_id(db, cat_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Thể loại ID {cat_id} không tồn tại.",
                )

        # 4. Verify unique ISBN and SKU
        if BookRepository.get_by_isbn(db, data.isbn):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Mã ISBN '{data.isbn}' đã được sử dụng bởi một đầu sách khác.",
            )
        if BookRepository.get_by_sku(db, data.sku):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Mã SKU '{data.sku}' đã được sử dụng.",
            )

        # 5. Create
        created_book = BookRepository.create_book(db, data)
        return to_book_detail_read(created_book)

    @classmethod
    def update_book(cls, db: Session, book_id: int, data: BookUpdate) -> BookDetailRead:
        """Update existing book publication."""
        book = BookRepository.get_by_id(db, book_id)
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy sách với ID {book_id}.",
            )

        # Check publisher if provided
        if data.publisher_id and not PublisherRepository.get_by_id(db, data.publisher_id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Nhà xuất bản ID {data.publisher_id} không tồn tại.",
            )

        updated_book = BookRepository.update_book(db, book, data)
        return to_book_detail_read(updated_book)

    @classmethod
    def delete_book(cls, db: Session, book_id: int) -> None:
        """Delete book record."""
        book = BookRepository.get_by_id(db, book_id)
        if not book:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Không tìm thấy sách với ID {book_id}.",
            )
        BookRepository.delete_book(db, book)

    # ========================================================================
    # CATEGORY OPERATIONS
    # ========================================================================

    @classmethod
    def get_categories(
        cls, db: Session, as_tree: bool = True
    ) -> List[Union[CategoryTreeRead, CategoryRead]]:
        """Fetch categories either as flat list or hierarchical tree."""
        if as_tree:
            roots = CategoryRepository.get_tree(db)
            result: List[CategoryTreeRead] = []
            for root in roots:
                sub_dtos = [
                    CategoryTreeRead(
                        id=sub.id,
                        name=sub.name,
                        slug=sub.slug,
                        description=sub.description,
                        parent_id=sub.parent_id,
                        display_order=sub.display_order,
                        created_at=sub.created_at,
                        book_count=CategoryRepository.count_books_in_category(db, sub.id),
                        subcategories=[],
                    )
                    for sub in (root.subcategories or [])
                ]
                result.append(
                    CategoryTreeRead(
                        id=root.id,
                        name=root.name,
                        slug=root.slug,
                        description=root.description,
                        parent_id=root.parent_id,
                        display_order=root.display_order,
                        created_at=root.created_at,
                        book_count=CategoryRepository.count_books_in_category(db, root.id),
                        subcategories=sub_dtos,
                    )
                )
            return result
        else:
            cats = CategoryRepository.get_all(db)
            return [
                CategoryRead(
                    id=c.id,
                    name=c.name,
                    slug=c.slug,
                    description=c.description,
                    parent_id=c.parent_id,
                    display_order=c.display_order,
                    created_at=c.created_at,
                    book_count=CategoryRepository.count_books_in_category(db, c.id),
                )
                for c in cats
            ]

    @classmethod
    def create_category(cls, db: Session, data: CategoryCreate) -> CategoryRead:
        if CategoryRepository.get_by_slug(db, data.slug or data.name):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Thể loại '{data.name}' đã tồn tại.",
            )
        category = CategoryRepository.create(db, data)
        return CategoryRead.model_validate(category)

    @classmethod
    def update_category(
        cls, db: Session, category_id: int, data: CategoryUpdate
    ) -> CategoryRead:
        category = CategoryRepository.get_by_id(db, category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Thể loại ID {category_id} không tồn tại.",
            )
        updated = CategoryRepository.update(db, category, data)
        return CategoryRead.model_validate(updated)

    @classmethod
    def delete_category(cls, db: Session, category_id: int) -> None:
        category = CategoryRepository.get_by_id(db, category_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Thể loại ID {category_id} không tồn tại.",
            )
        CategoryRepository.delete(db, category)

    # ========================================================================
    # AUTHOR OPERATIONS
    # ========================================================================

    @classmethod
    def get_authors(
        cls, db: Session, skip: int = 0, limit: int = 100, query: Optional[str] = None
    ) -> List[AuthorRead]:
        authors = AuthorRepository.get_all(db, skip=skip, limit=limit, query=query)
        return [AuthorRead.model_validate(a) for a in authors]

    @classmethod
    def create_author(cls, db: Session, data: AuthorCreate) -> AuthorRead:
        author = AuthorRepository.create(db, data)
        return AuthorRead.model_validate(author)

    @classmethod
    def update_author(cls, db: Session, author_id: int, data: AuthorUpdate) -> AuthorRead:
        author = AuthorRepository.get_by_id(db, author_id)
        if not author:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tác giả ID {author_id} không tồn tại.",
            )
        updated = AuthorRepository.update(db, author, data)
        return AuthorRead.model_validate(updated)

    @classmethod
    def delete_author(cls, db: Session, author_id: int) -> None:
        author = AuthorRepository.get_by_id(db, author_id)
        if not author:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Tác giả ID {author_id} không tồn tại.",
            )
        AuthorRepository.delete(db, author)

    # ========================================================================
    # PUBLISHER OPERATIONS
    # ========================================================================

    @classmethod
    def get_publishers(
        cls, db: Session, skip: int = 0, limit: int = 100
    ) -> List[PublisherRead]:
        pubs = PublisherRepository.get_all(db, skip=skip, limit=limit)
        return [PublisherRead.model_validate(p) for p in pubs]

    @classmethod
    def create_publisher(cls, db: Session, data: PublisherCreate) -> PublisherRead:
        pub = PublisherRepository.create(db, data)
        return PublisherRead.model_validate(pub)

    @classmethod
    def update_publisher(
        cls, db: Session, publisher_id: int, data: PublisherUpdate
    ) -> PublisherRead:
        pub = PublisherRepository.get_by_id(db, publisher_id)
        if not pub:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Nhà xuất bản ID {publisher_id} không tồn tại.",
            )
        updated = PublisherRepository.update(db, pub, data)
        return PublisherRead.model_validate(updated)

    @classmethod
    def delete_publisher(cls, db: Session, publisher_id: int) -> None:
        pub = PublisherRepository.get_by_id(db, publisher_id)
        if not pub:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Nhà xuất bản ID {publisher_id} không tồn tại.",
            )
        PublisherRepository.delete(db, pub)
