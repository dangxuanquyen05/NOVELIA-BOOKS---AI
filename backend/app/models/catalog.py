"""Book catalog models: Books, Categories, Authors, Publishers, and Images."""

from datetime import datetime, timezone, date
from sqlalchemy import (
    BigInteger,
    Boolean,
    Column,
    Date,
    DateTime,
    DECIMAL,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship

from app.database.connection import Base


class Publisher(Base):
    """Book publishing house."""

    __tablename__ = "publishers"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(150), nullable=False, unique=True, index=True)
    slug = Column(String(170), nullable=False, unique=True, index=True)
    contact_info = Column(String(255), nullable=True)
    address = Column(String(255), nullable=True)
    website = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    books = relationship("Book", back_populates="publisher", cascade="all, delete-orphan")


class Author(Base):
    """Book author metadata."""

    __tablename__ = "authors"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(150), nullable=False, index=True)
    slug = Column(String(170), nullable=False, unique=True, index=True)
    bio = Column(Text, nullable=True)
    avatar_url = Column(String(500), nullable=True)
    birth_year = Column(Integer, nullable=True)
    nationality = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    book_authors = relationship("BookAuthor", back_populates="author", cascade="all, delete-orphan")


class Category(Base):
    """Book genre and hierarchical taxonomy."""

    __tablename__ = "categories"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False, unique=True, index=True)
    slug = Column(String(120), nullable=False, unique=True, index=True)
    description = Column(String(255), nullable=True)
    parent_id = Column(BigInteger, ForeignKey("categories.id", ondelete="SET NULL"), nullable=True)
    display_order = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    subcategories = relationship("Category", backref="parent", remote_side=[id])
    book_categories = relationship("BookCategory", back_populates="category", cascade="all, delete-orphan")


class Book(Base):
    """Core book publication entity."""

    __tablename__ = "books"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    isbn = Column(String(20), nullable=False, unique=True, index=True)
    sku = Column(String(50), nullable=False, unique=True, index=True)
    title = Column(String(255), nullable=False, index=True)
    slug = Column(String(280), nullable=False, unique=True, index=True)
    publisher_id = Column(BigInteger, ForeignKey("publishers.id", ondelete="RESTRICT"), nullable=False)
    price = Column(DECIMAL(12, 2), nullable=False)
    original_price = Column(DECIMAL(12, 2), nullable=False)
    page_count = Column(Integer, nullable=True)
    dimension = Column(String(50), nullable=True)
    weight_grams = Column(Integer, default=300, nullable=False)
    cover_type = Column(String(30), default="PAPERBACK", nullable=False)  # PAPERBACK, HARDCOVER
    description = Column(Text, nullable=True)
    sample_text = Column(Text, nullable=True)
    cover_image_url = Column(String(500), nullable=False)
    status = Column(String(30), default="ACTIVE", nullable=False, index=True)  # DRAFT, ACTIVE, OUT_OF_STOCK, DISCONTINUED
    published_date = Column(Date, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(
        DateTime,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    __table_args__ = (
        Index("idx_books_publisher", "publisher_id"),
        Index("idx_books_status", "status"),
        Index("idx_books_price", "price"),
    )

    # Relationships
    publisher = relationship("Publisher", back_populates="books")
    authors = relationship("BookAuthor", back_populates="book", cascade="all, delete-orphan")
    categories = relationship("BookCategory", back_populates="book", cascade="all, delete-orphan")
    images = relationship("BookImage", back_populates="book", cascade="all, delete-orphan")
    inventory = relationship("Inventory", back_populates="book", uselist=False, cascade="all, delete-orphan")
    reviews = relationship("Review", back_populates="book", cascade="all, delete-orphan")


class BookAuthor(Base):
    """Many-to-Many association between Books and Authors."""

    __tablename__ = "book_authors"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    book_id = Column(BigInteger, ForeignKey("books.id", ondelete="CASCADE"), nullable=False)
    author_id = Column(BigInteger, ForeignKey("authors.id", ondelete="RESTRICT"), nullable=False)
    is_primary = Column(Boolean, default=True, nullable=False)
    order_index = Column(Integer, default=0, nullable=False)

    __table_args__ = (
        UniqueConstraint("book_id", "author_id", name="uq_book_author"),
        Index("idx_book_authors_book", "book_id"),
        Index("idx_book_authors_author", "author_id"),
    )

    book = relationship("Book", back_populates="authors")
    author = relationship("Author", back_populates="book_authors")


class BookCategory(Base):
    """Many-to-Many association between Books and Categories."""

    __tablename__ = "book_categories"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    book_id = Column(BigInteger, ForeignKey("books.id", ondelete="CASCADE"), nullable=False)
    category_id = Column(BigInteger, ForeignKey("categories.id", ondelete="CASCADE"), nullable=False)

    __table_args__ = (
        UniqueConstraint("book_id", "category_id", name="uq_book_category"),
        Index("idx_book_categories_book", "book_id"),
        Index("idx_book_categories_category", "category_id"),
    )

    book = relationship("Book", back_populates="categories")
    category = relationship("Category", back_populates="book_categories")


class BookImage(Base):
    """Gallery images for books."""

    __tablename__ = "book_images"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    book_id = Column(BigInteger, ForeignKey("books.id", ondelete="CASCADE"), nullable=False)
    image_url = Column(String(500), nullable=False)
    alt_text = Column(String(255), nullable=True)
    display_order = Column(Integer, default=0, nullable=False)
    is_cover = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)

    __table_args__ = (
        Index("idx_book_images_book", "book_id"),
    )

    book = relationship("Book", back_populates="images")
