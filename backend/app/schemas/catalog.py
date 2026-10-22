"""Pydantic schemas for Book Catalog, Categories, Authors, Publishers, and Filters."""

from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field


# ============================================================================
# PUBLISHER SCHEMAS
# ============================================================================


class PublisherBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=150, description="Publisher name")
    slug: str = Field(..., min_length=1, max_length=170, description="URL-friendly slug")
    contact_info: Optional[str] = Field(None, max_length=255)
    address: Optional[str] = Field(None, max_length=255)
    website: Optional[str] = Field(None, max_length=255)


class PublisherCreate(PublisherBase):
    slug: Optional[str] = Field(None, max_length=170)


class PublisherUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=150)
    slug: Optional[str] = Field(None, min_length=1, max_length=170)
    contact_info: Optional[str] = Field(None, max_length=255)
    address: Optional[str] = Field(None, max_length=255)
    website: Optional[str] = Field(None, max_length=255)


class PublisherRead(PublisherBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


# ============================================================================
# AUTHOR SCHEMAS
# ============================================================================


class AuthorBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=150, description="Author full name")
    slug: str = Field(..., min_length=1, max_length=170, description="URL-friendly slug")
    bio: Optional[str] = None
    avatar_url: Optional[str] = Field(None, max_length=500)
    birth_year: Optional[int] = None
    nationality: Optional[str] = Field(None, max_length=100)


class AuthorCreate(AuthorBase):
    slug: Optional[str] = Field(None, max_length=170)


class AuthorUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=150)
    slug: Optional[str] = Field(None, min_length=1, max_length=170)
    bio: Optional[str] = None
    avatar_url: Optional[str] = Field(None, max_length=500)
    birth_year: Optional[int] = None
    nationality: Optional[str] = Field(None, max_length=100)


class AuthorRead(AuthorBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


# ============================================================================
# CATEGORY SCHEMAS
# ============================================================================


class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100, description="Category name")
    slug: str = Field(..., min_length=1, max_length=120, description="URL-friendly slug")
    description: Optional[str] = Field(None, max_length=255)
    parent_id: Optional[int] = None
    display_order: int = Field(0, ge=0)


class CategoryCreate(CategoryBase):
    slug: Optional[str] = Field(None, max_length=120)


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    slug: Optional[str] = Field(None, min_length=1, max_length=120)
    description: Optional[str] = Field(None, max_length=255)
    parent_id: Optional[int] = None
    display_order: Optional[int] = Field(None, ge=0)


class CategoryRead(CategoryBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    book_count: int = 0


class CategoryTreeRead(CategoryRead):
    subcategories: List["CategoryTreeRead"] = []


# ============================================================================
# BOOK IMAGES & ASSOCIATIONS SCHEMAS
# ============================================================================


class BookImageBase(BaseModel):
    image_url: str = Field(..., max_length=500)
    alt_text: Optional[str] = Field(None, max_length=255)
    display_order: int = 0
    is_cover: bool = False


class BookImageCreate(BookImageBase):
    pass


class BookImageRead(BookImageBase):
    model_config = ConfigDict(from_attributes=True)

    id: int


class BookAuthorRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    author_id: int
    name: str
    slug: str
    is_primary: bool = True
    order_index: int = 0


class BookCategoryRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    category_id: int
    name: str
    slug: str


# ============================================================================
# BOOK SCHEMAS
# ============================================================================


class BookCreate(BaseModel):
    isbn: str = Field(..., min_length=10, max_length=20, description="ISBN-10 or ISBN-13")
    sku: str = Field(..., min_length=3, max_length=50, description="Unique store SKU")
    title: str = Field(..., min_length=1, max_length=255)
    slug: Optional[str] = Field(None, max_length=280)
    publisher_id: int
    price: Decimal = Field(..., gt=0, decimal_places=2, max_digits=12)
    original_price: Decimal = Field(..., gt=0, decimal_places=2, max_digits=12)
    page_count: Optional[int] = Field(None, gt=0)
    dimension: Optional[str] = Field(None, max_length=50)
    weight_grams: int = Field(300, gt=0)
    cover_type: str = Field("PAPERBACK", description="PAPERBACK or HARDCOVER")
    description: Optional[str] = None
    sample_text: Optional[str] = None
    cover_image_url: str = Field(..., max_length=500)
    status: str = Field("ACTIVE", description="DRAFT, ACTIVE, OUT_OF_STOCK, DISCONTINUED")
    published_date: Optional[date] = None

    author_ids: List[int] = Field(..., min_length=1, description="List of author IDs")
    primary_author_id: Optional[int] = None
    category_ids: List[int] = Field(..., min_length=1, description="List of category IDs")
    images: Optional[List[BookImageCreate]] = None
    initial_stock: int = Field(50, ge=0)


class BookUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    slug: Optional[str] = Field(None, max_length=280)
    publisher_id: Optional[int] = None
    price: Optional[Decimal] = Field(None, gt=0, decimal_places=2, max_digits=12)
    original_price: Optional[Decimal] = Field(None, gt=0, decimal_places=2, max_digits=12)
    page_count: Optional[int] = Field(None, gt=0)
    dimension: Optional[str] = Field(None, max_length=50)
    weight_grams: Optional[int] = Field(None, gt=0)
    cover_type: Optional[str] = None
    description: Optional[str] = None
    sample_text: Optional[str] = None
    cover_image_url: Optional[str] = Field(None, max_length=500)
    status: Optional[str] = None
    published_date: Optional[date] = None
    author_ids: Optional[List[int]] = None
    category_ids: Optional[List[int]] = None


class BookListRead(BaseModel):
    """Compact summary schema for catalog grids, search results, and cards."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    isbn: str
    sku: str
    title: str
    slug: str
    price: Decimal
    original_price: Decimal
    discount_percent: int = 0
    cover_image_url: str
    cover_type: str
    status: str
    primary_author: Optional[str] = None
    authors: List[BookAuthorRead] = []
    categories: List[BookCategoryRead] = []
    stock_available: int = 0
    is_in_stock: bool = True
    created_at: datetime


class BookDetailRead(BookListRead):
    """Full detail schema for product detail page and modals."""
    publisher: Optional[PublisherRead] = None
    page_count: Optional[int] = None
    dimension: Optional[str] = None
    weight_grams: int = 300
    description: Optional[str] = None
    sample_text: Optional[str] = None
    published_date: Optional[date] = None
    images: List[BookImageRead] = []
    updated_at: datetime


# ============================================================================
# SEARCH, FILTER & PAGINATION SCHEMAS
# ============================================================================


class BookFilterParams(BaseModel):
    query: Optional[str] = Field(None, description="Search keyword matching title, ISBN, or author name")
    category_slug: Optional[str] = Field(None, description="Category slug filter")
    category_id: Optional[int] = Field(None, description="Category ID filter")
    author_id: Optional[int] = Field(None, description="Author ID filter")
    publisher_id: Optional[int] = Field(None, description="Publisher ID filter")
    min_price: Optional[Decimal] = Field(None, ge=0, description="Minimum price filter")
    max_price: Optional[Decimal] = Field(None, ge=0, description="Maximum price filter")
    cover_type: Optional[str] = Field(None, description="PAPERBACK or HARDCOVER")
    status: Optional[str] = Field("ACTIVE", description="ACTIVE, DRAFT, OUT_OF_STOCK, or ALL")
    sort_by: Optional[str] = Field(
        "newest",
        description="Sort by: newest, price_asc, price_desc, title_asc, title_desc, discount_desc"
    )
    page: int = Field(1, ge=1, description="Page number starting at 1")
    page_size: int = Field(12, ge=1, le=100, description="Page size limit (max 100)")


class PaginatedBooksResponse(BaseModel):
    items: List[BookListRead]
    total: int
    page: int
    page_size: int
    total_pages: int
