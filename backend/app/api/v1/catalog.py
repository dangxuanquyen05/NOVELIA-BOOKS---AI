"""Catalog and Storefront API endpoints for Books, Categories, Authors, and Publishers."""

from decimal import Decimal
from typing import List, Optional, Union
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.database.connection import get_db
from app.models.user import User
from app.schemas.auth import MessageResponse
from app.schemas.catalog import (
    AuthorCreate,
    AuthorRead,
    AuthorUpdate,
    BookCreate,
    BookDetailRead,
    BookFilterParams,
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
from app.services.catalog_service import CatalogService

router = APIRouter(prefix="/catalog", tags=["Book Catalog & Storefront"])


# ============================================================================
# PUBLIC STOREFRONT ENDPOINTS
# ============================================================================


@router.get(
    "/books",
    response_model=PaginatedBooksResponse,
    summary="List and filter books with pagination",
)
def list_books(
    query: Optional[str] = Query(None, description="Search term for Title, ISBN, or Author"),
    category_slug: Optional[str] = Query(None, description="Category slug"),
    category_id: Optional[int] = Query(None, description="Category ID"),
    author_id: Optional[int] = Query(None, description="Author ID"),
    publisher_id: Optional[int] = Query(None, description="Publisher ID"),
    min_price: Optional[Decimal] = Query(None, ge=0, description="Minimum price filter"),
    max_price: Optional[Decimal] = Query(None, ge=0, description="Maximum price filter"),
    cover_type: Optional[str] = Query(None, description="PAPERBACK or HARDCOVER"),
    status: Optional[str] = Query("ACTIVE", description="ACTIVE, DRAFT, OUT_OF_STOCK, or ALL"),
    sort_by: Optional[str] = Query(
        "newest",
        description="Sort by: newest, price_asc, price_desc, title_asc, title_desc, discount_desc",
    ),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(12, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
):
    """Retrieve catalog books with multi-criteria filtering, search, sorting, and pagination."""
    params = BookFilterParams(
        query=query,
        category_slug=category_slug,
        category_id=category_id,
        author_id=author_id,
        publisher_id=publisher_id,
        min_price=min_price,
        max_price=max_price,
        cover_type=cover_type,
        status=status,
        sort_by=sort_by,
        page=page,
        page_size=page_size,
    )
    return CatalogService.get_books(db, params)


@router.get(
    "/books/featured",
    response_model=List[BookListRead],
    summary="Get featured or promotional books for storefront showcase",
)
def get_featured_books(
    limit: int = Query(8, ge=1, le=24),
    db: Session = Depends(get_db),
):
    """Retrieve top discounted and newest featured books."""
    return CatalogService.get_featured_books(db, limit=limit)


@router.get(
    "/books/{identifier}",
    response_model=BookDetailRead,
    summary="Get complete book details by slug or ID",
)
def get_book_detail(
    identifier: str,
    db: Session = Depends(get_db),
):
    """Retrieve detailed book view by slug or numeric ID."""
    return CatalogService.get_book_by_slug_or_id(db, identifier)


@router.get(
    "/books/{book_id}/related",
    response_model=List[BookListRead],
    summary="Get related book recommendations",
)
def get_related_books(
    book_id: int,
    limit: int = Query(4, ge=1, le=12),
    db: Session = Depends(get_db),
):
    """Find books sharing categories or authors with the given book."""
    return CatalogService.get_related_books(db, book_id=book_id, limit=limit)


@router.get(
    "/categories",
    response_model=List[Union[CategoryTreeRead, CategoryRead]],
    summary="List categories hierarchical tree or flat list",
)
def list_categories(
    as_tree: bool = Query(True, description="Return nested hierarchy when true"),
    db: Session = Depends(get_db),
):
    """Fetch genre taxonomy."""
    return CatalogService.get_categories(db, as_tree=as_tree)


@router.get(
    "/authors",
    response_model=List[AuthorRead],
    summary="List authors in the catalog",
)
def list_authors(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    query: Optional[str] = Query(None, description="Search author by name"),
    db: Session = Depends(get_db),
):
    """Retrieve authors with optional name filtering."""
    return CatalogService.get_authors(db, skip=skip, limit=limit, query=query)


@router.get(
    "/publishers",
    response_model=List[PublisherRead],
    summary="List publishing houses",
)
def list_publishers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=200),
    db: Session = Depends(get_db),
):
    """Retrieve publishers."""
    return CatalogService.get_publishers(db, skip=skip, limit=limit)


# ============================================================================
# PROTECTED MANAGEMENT ENDPOINTS (STAFF & ADMIN)
# ============================================================================


@router.post(
    "/books",
    response_model=BookDetailRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new book (Staff & Admin)",
)
def create_book(
    data: BookCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("STAFF", "ADMIN")),
):
    """Register a new book into the catalog."""
    return CatalogService.create_book(db, data)


@router.put(
    "/books/{book_id}",
    response_model=BookDetailRead,
    summary="Update existing book (Staff & Admin)",
)
def update_book(
    book_id: int,
    data: BookUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("STAFF", "ADMIN")),
):
    """Update book information, authors, or categories."""
    return CatalogService.update_book(db, book_id, data)


@router.delete(
    "/books/{book_id}",
    response_model=MessageResponse,
    summary="Delete book (Admin only)",
)
def delete_book(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN")),
):
    """Delete a book record."""
    CatalogService.delete_book(db, book_id)
    return MessageResponse(message=f"Đã xóa sách với ID {book_id} thành công.")


@router.post(
    "/categories",
    response_model=CategoryRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create category (Staff & Admin)",
)
def create_category(
    data: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("STAFF", "ADMIN")),
):
    return CatalogService.create_category(db, data)


@router.put(
    "/categories/{category_id}",
    response_model=CategoryRead,
    summary="Update category (Staff & Admin)",
)
def update_category(
    category_id: int,
    data: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("STAFF", "ADMIN")),
):
    return CatalogService.update_category(db, category_id, data)


@router.delete(
    "/categories/{category_id}",
    response_model=MessageResponse,
    summary="Delete category (Admin only)",
)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN")),
):
    CatalogService.delete_category(db, category_id)
    return MessageResponse(message=f"Đã xóa thể loại với ID {category_id} thành công.")


@router.post(
    "/authors",
    response_model=AuthorRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create author (Staff & Admin)",
)
def create_author(
    data: AuthorCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("STAFF", "ADMIN")),
):
    return CatalogService.create_author(db, data)


@router.put(
    "/authors/{author_id}",
    response_model=AuthorRead,
    summary="Update author (Staff & Admin)",
)
def update_author(
    author_id: int,
    data: AuthorUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("STAFF", "ADMIN")),
):
    return CatalogService.update_author(db, author_id, data)


@router.delete(
    "/authors/{author_id}",
    response_model=MessageResponse,
    summary="Delete author (Admin only)",
)
def delete_author(
    author_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN")),
):
    CatalogService.delete_author(db, author_id)
    return MessageResponse(message=f"Đã xóa tác giả với ID {author_id} thành công.")


@router.post(
    "/publishers",
    response_model=PublisherRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create publisher (Staff & Admin)",
)
def create_publisher(
    data: PublisherCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("STAFF", "ADMIN")),
):
    return CatalogService.create_publisher(db, data)


@router.put(
    "/publishers/{publisher_id}",
    response_model=PublisherRead,
    summary="Update publisher (Staff & Admin)",
)
def update_publisher(
    publisher_id: int,
    data: PublisherUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("STAFF", "ADMIN")),
):
    return CatalogService.update_publisher(db, publisher_id, data)


@router.delete(
    "/publishers/{publisher_id}",
    response_model=MessageResponse,
    summary="Delete publisher (Admin only)",
)
def delete_publisher(
    publisher_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles("ADMIN")),
):
    CatalogService.delete_publisher(db, publisher_id)
    return MessageResponse(message=f"Đã xóa nhà xuất bản với ID {publisher_id} thành công.")
