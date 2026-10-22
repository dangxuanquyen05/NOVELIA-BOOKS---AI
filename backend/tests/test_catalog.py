"""Comprehensive test suite for Phase 4 Book Catalog, Storefront APIs, and RBAC."""

from decimal import Decimal
from unittest.mock import MagicMock, patch
import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient

from app.database.connection import get_db
from app.main import app
from app.models.catalog import Author, Book, BookAuthor, BookCategory, BookImage, Category, Publisher
from app.models.inventory import Inventory
from app.models.user import Role, User, UserRole
from app.schemas.catalog import (
    AuthorCreate,
    BookCreate,
    BookDetailRead,
    BookFilterParams,
    BookListRead,
    BookUpdate,
    CategoryCreate,
    PaginatedBooksResponse,
    PublisherCreate,
)
from app.services.catalog_service import (
    CatalogService,
    to_book_detail_read,
    to_book_list_read,
)

client = TestClient(app)


# ============================================================================
# FIXTURES & MOCK HELPERS
# ============================================================================


def make_mock_user(role_name: str, user_id: int = 1) -> User:
    """Create a mock user with specified RBAC role."""
    user = MagicMock(spec=User)
    user.id = user_id
    user.email = f"{role_name.lower()}@novelia.vn"
    user.is_active = True

    role = MagicMock(spec=Role)
    role.name = role_name

    user_role = MagicMock(spec=UserRole)
    user_role.role = role
    user.roles = [user_role]
    return user


def make_mock_book(
    book_id: int = 1,
    title: str = "Nhà Giả Kim",
    isbn: str = "9786045622544",
    sku: str = "NOV-NGK-01",
    price: Decimal = Decimal("79000.00"),
    original_price: Decimal = Decimal("95000.00"),
    physical_stock: int = 45,
    reserved_stock: int = 5,
    status_str: str = "ACTIVE",
) -> Book:
    """Generate a realistic mock Book with relationships."""
    book = MagicMock(spec=Book)
    book.id = book_id
    book.title = title
    book.slug = "nha-gia-kim"
    book.isbn = isbn
    book.sku = sku
    book.price = price
    book.original_price = original_price
    book.page_count = 228
    book.dimension = "13 x 20.5 cm"
    book.weight_grams = 280
    book.cover_type = "PAPERBACK"
    book.description = "Cuốn sách kinh điển về hành trình tìm kiếm vận mệnh."
    book.sample_text = "Khi bạn khao khát một điều gì đó, cả vũ trụ sẽ hợp lực..."
    book.cover_image_url = "https://images.novelia.vn/books/nhagiakim.jpg"
    book.status = status_str
    book.published_date = None
    book.created_at = "2026-01-01T00:00:00Z"
    book.updated_at = "2026-01-01T00:00:00Z"

    # Publisher
    pub = MagicMock(spec=Publisher)
    pub.id = 1
    pub.name = "NXB Hội Nhà Văn"
    pub.slug = "nxb-hoi-nha-van"
    pub.contact_info = "contact@hoinhavan.vn"
    pub.address = "Hà Nội"
    pub.website = "https://hoinhavan.vn"
    pub.created_at = "2026-01-01T00:00:00Z"
    book.publisher = pub

    # Authors
    author = MagicMock(spec=Author)
    author.id = 1
    author.name = "Paulo Coelho"
    author.slug = "paulo-coelho"
    author.bio = "Tác giả nổi tiếng người Brazil."
    author.avatar_url = "https://images.novelia.vn/authors/paulocoelho.jpg"
    author.birth_year = 1947
    author.nationality = "Brazil"
    author.created_at = "2026-01-01T00:00:00Z"

    book_author = MagicMock(spec=BookAuthor)
    book_author.author = author
    book_author.is_primary = True
    book_author.order_index = 0
    book.authors = [book_author]

    # Categories
    cat = MagicMock(spec=Category)
    cat.id = 1
    cat.name = "Văn Học Kinh Điển"
    cat.slug = "van-hoc-kinh-dien"
    cat.description = "Tác phẩm văn học bất hủ"
    cat.parent_id = None
    cat.display_order = 1
    cat.created_at = "2026-01-01T00:00:00Z"

    book_cat = MagicMock(spec=BookCategory)
    book_cat.category = cat
    book.categories = [book_cat]

    # Inventory
    inv = MagicMock(spec=Inventory)
    inv.id = 1
    inv.book_id = book_id
    inv.physical_stock = physical_stock
    inv.reserved_stock = reserved_stock
    inv.available_stock = physical_stock - reserved_stock
    book.inventory = inv

    # Images
    img = MagicMock(spec=BookImage)
    img.id = 1
    img.image_url = "https://images.novelia.vn/books/nhagiakim.jpg"
    img.alt_text = "Bìa trước Nhà Giả Kim"
    img.display_order = 0
    img.is_cover = True
    book.images = [img]

    return book


# ============================================================================
# TEST CASES: CATALOG TRANSFORMATIONS & BUSINESS LOGIC
# ============================================================================


class TestCatalogTransformations:
    """Verify DTO mappings, discount computations, and stock calculations."""

    def test_book_dto_discount_and_stock_calculation(self):
        book = make_mock_book(
            price=Decimal("80000.00"),
            original_price=Decimal("100000.00"),
            physical_stock=50,
            reserved_stock=10,
        )
        dto = to_book_list_read(book)

        assert dto.title == "Nhà Giả Kim"
        assert dto.discount_percent == 20
        assert dto.stock_available == 40
        assert dto.is_in_stock is True
        assert dto.primary_author == "Paulo Coelho"
        assert len(dto.categories) == 1
        assert dto.categories[0].name == "Văn Học Kinh Điển"

    def test_out_of_stock_calculation(self):
        book = make_mock_book(
            physical_stock=10,
            reserved_stock=10,
            status_str="ACTIVE",
        )
        dto = to_book_list_read(book)
        assert dto.stock_available == 0
        assert dto.is_in_stock is False


class TestCatalogServiceValidations:
    """Verify service level business validations (existence, conflict checks)."""

    def test_create_book_missing_publisher_raises_bad_request(self):
        mock_db = MagicMock()
        book_in = BookCreate(
            isbn="9786040000011",
            sku="NOV-TEST-01",
            title="Sách Thử Nghiệm",
            publisher_id=999,  # Non-existent
            price=Decimal("100000.00"),
            original_price=Decimal("120000.00"),
            cover_image_url="https://novelia.vn/test.jpg",
            author_ids=[1],
            category_ids=[1],
        )

        with patch("app.repositories.catalog_repo.PublisherRepository.get_by_id", return_value=None):
            with pytest.raises(HTTPException) as exc:
                CatalogService.create_book(mock_db, book_in)
            assert exc.value.status_code == status.HTTP_400_BAD_REQUEST
            assert "Nhà xuất bản" in exc.value.detail

    def test_create_book_duplicate_isbn_raises_conflict(self):
        mock_db = MagicMock()
        book_in = BookCreate(
            isbn="9786045622544",
            sku="NOV-UNIQUE-01",
            title="Sách Trùng ISBN",
            publisher_id=1,
            price=Decimal("50000.00"),
            original_price=Decimal("50000.00"),
            cover_image_url="https://novelia.vn/test.jpg",
            author_ids=[1],
            category_ids=[1],
        )

        with patch("app.repositories.catalog_repo.PublisherRepository.get_by_id", return_value=MagicMock()):
            with patch("app.repositories.catalog_repo.AuthorRepository.get_by_id", return_value=MagicMock()):
                with patch("app.repositories.catalog_repo.CategoryRepository.get_by_id", return_value=MagicMock()):
                    with patch("app.repositories.catalog_repo.BookRepository.get_by_isbn", return_value=MagicMock()):
                        with pytest.raises(HTTPException) as exc:
                            CatalogService.create_book(mock_db, book_in)
                        assert exc.value.status_code == status.HTTP_409_CONFLICT
                        assert "ISBN" in exc.value.detail


# ============================================================================
# TEST CASES: STOREFRONT PUBLIC ENDPOINTS
# ============================================================================


class TestStorefrontPublicEndpoints:
    """Verify storefront public query endpoints (browsing, filters, search)."""

    def test_list_books_endpoint(self):
        mock_book = make_mock_book()
        with patch("app.repositories.catalog_repo.BookRepository.list_books", return_value=([mock_book], 1)):
            response = client.get("/api/v1/catalog/books?page=1&page_size=10")
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["total"] == 1
            assert data["page"] == 1
            assert data["total_pages"] == 1
            assert len(data["items"]) == 1
            assert data["items"][0]["title"] == "Nhà Giả Kim"
            assert data["items"][0]["primary_author"] == "Paulo Coelho"

    def test_list_books_search_query(self):
        mock_book = make_mock_book(title="Chiến Binh Cầu Vồng")
        with patch("app.repositories.catalog_repo.BookRepository.list_books", return_value=([mock_book], 1)) as mock_list:
            response = client.get("/api/v1/catalog/books?query=Chiến+Binh")
            assert response.status_code == status.HTTP_200_OK
            call_params = mock_list.call_args[0][1]
            assert call_params.query == "Chiến Binh"

    def test_get_book_detail_by_slug_success(self):
        mock_book = make_mock_book()
        with patch("app.repositories.catalog_repo.BookRepository.get_by_slug", return_value=mock_book):
            response = client.get("/api/v1/catalog/books/nha-gia-kim")
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert data["title"] == "Nhà Giả Kim"
            assert data["publisher"]["name"] == "NXB Hội Nhà Văn"
            assert data["stock_available"] == 40
            assert len(data["images"]) == 1

    def test_get_book_detail_not_found(self):
        with patch("app.repositories.catalog_repo.BookRepository.get_by_slug", return_value=None):
            with patch("app.repositories.catalog_repo.BookRepository.get_by_id", return_value=None):
                response = client.get("/api/v1/catalog/books/non-existent-book")
                assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_get_featured_books(self):
        mock_book = make_mock_book()
        with patch("app.repositories.catalog_repo.BookRepository.get_featured_books", return_value=[mock_book]):
            response = client.get("/api/v1/catalog/books/featured?limit=4")
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data) == 1
            assert data[0]["title"] == "Nhà Giả Kim"

    def test_get_related_books(self):
        mock_book = make_mock_book(book_id=2, title="Người Đua Diều")
        with patch("app.repositories.catalog_repo.BookRepository.get_related_books", return_value=[mock_book]):
            response = client.get("/api/v1/catalog/books/1/related?limit=3")
            assert response.status_code == status.HTTP_200_OK
            data = response.json()
            assert len(data) == 1
            assert data[0]["title"] == "Người Đua Diều"

    def test_get_categories_tree(self):
        mock_cat = MagicMock(spec=Category)
        mock_cat.id = 1
        mock_cat.name = "Văn Học"
        mock_cat.slug = "van-hoc"
        mock_cat.description = "Sách văn học"
        mock_cat.parent_id = None
        mock_cat.display_order = 1
        mock_cat.created_at = "2026-01-01T00:00:00Z"
        mock_cat.subcategories = []

        with patch("app.repositories.catalog_repo.CategoryRepository.get_tree", return_value=[mock_cat]):
            with patch("app.repositories.catalog_repo.CategoryRepository.count_books_in_category", return_value=12):
                response = client.get("/api/v1/catalog/categories?as_tree=true")
                assert response.status_code == status.HTTP_200_OK
                data = response.json()
                assert len(data) == 1
                assert data[0]["name"] == "Văn Học"
                assert data[0]["book_count"] == 12


# ============================================================================
# TEST CASES: RBAC ENFORCEMENT ON MANAGEMENT ENDPOINTS
# ============================================================================


class TestCatalogRBACProtection:
    """Verify that mutating endpoints strictly enforce STAFF and ADMIN roles."""

    def test_create_book_unauthenticated_rejected(self):
        payload = {
            "isbn": "9786045622544",
            "sku": "NOV-TEST-01",
            "title": "Unauthorized Book",
            "publisher_id": 1,
            "price": "90000.00",
            "original_price": "100000.00",
            "cover_image_url": "https://test.jpg",
            "author_ids": [1],
            "category_ids": [1],
        }
        response = client.post("/api/v1/catalog/books", json=payload)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_book_as_customer_rejected_with_403(self):
        from app.api.deps import get_current_user
        customer = make_mock_user("CUSTOMER")
        payload = {
            "isbn": "9786045622544",
            "sku": "NOV-TEST-01",
            "title": "Unauthorized Book",
            "publisher_id": 1,
            "price": "90000.00",
            "original_price": "100000.00",
            "cover_image_url": "https://test.jpg",
            "author_ids": [1],
            "category_ids": [1],
        }
        app.dependency_overrides[get_current_user] = lambda: customer
        try:
            with patch("app.repositories.user_repo.UserRepository.get_user_role_names", return_value=["CUSTOMER"]):
                response = client.post("/api/v1/catalog/books", json=payload)
                assert response.status_code == status.HTTP_403_FORBIDDEN
        finally:
            app.dependency_overrides.clear()

    def test_create_book_as_staff_permitted(self):
        from app.api.deps import get_current_user
        staff = make_mock_user("STAFF")
        mock_book = make_mock_book()
        payload = {
            "isbn": "9786045622544",
            "sku": "NOV-TEST-01",
            "title": "Nhà Giả Kim",
            "publisher_id": 1,
            "price": "79000.00",
            "original_price": "95000.00",
            "cover_image_url": "https://images.novelia.vn/books/nhagiakim.jpg",
            "author_ids": [1],
            "category_ids": [1],
            "initial_stock": 50,
        }
        app.dependency_overrides[get_current_user] = lambda: staff
        try:
            with patch("app.repositories.user_repo.UserRepository.get_user_role_names", return_value=["STAFF"]):
                with patch("app.services.catalog_service.CatalogService.create_book", return_value=to_book_detail_read(mock_book)):
                    response = client.post("/api/v1/catalog/books", json=payload)
                    assert response.status_code == status.HTTP_201_CREATED
                    data = response.json()
                    assert data["title"] == "Nhà Giả Kim"
        finally:
            app.dependency_overrides.clear()

    def test_delete_book_as_staff_rejected_with_403(self):
        """Staff can edit books, but deletion is strictly ADMIN only."""
        from app.api.deps import get_current_user
        staff = make_mock_user("STAFF")
        app.dependency_overrides[get_current_user] = lambda: staff
        try:
            with patch("app.repositories.user_repo.UserRepository.get_user_role_names", return_value=["STAFF"]):
                response = client.delete("/api/v1/catalog/books/1")
                assert response.status_code == status.HTTP_403_FORBIDDEN
        finally:
            app.dependency_overrides.clear()

    def test_delete_book_as_admin_permitted(self):
        from app.api.deps import get_current_user
        admin = make_mock_user("ADMIN")
        app.dependency_overrides[get_current_user] = lambda: admin
        try:
            with patch("app.repositories.user_repo.UserRepository.get_user_role_names", return_value=["ADMIN"]):
                with patch("app.services.catalog_service.CatalogService.delete_book", return_value=None):
                    response = client.delete("/api/v1/catalog/books/1")
                    assert response.status_code == status.HTTP_200_OK
                    assert "thành công" in response.json()["message"]
        finally:
            app.dependency_overrides.clear()

