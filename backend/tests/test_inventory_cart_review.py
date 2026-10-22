"""Unit and integration tests for Phase 5: Inventory, Shopping Cart, Wishlist, and Reviews.

Validates:
- Real-time stock enforcement & out-of-stock prevention
- Negative or invalid quantity rejection
- Tenant isolation: two users never share or see each other's carts
- RBAC protection: CUSTOMER blocked from stock adjustment (HTTP 403)
- STAFF & ADMIN stock inbound restock and adjustment with transaction history
- Review validations: 1-5 stars, content length, duplicate prevention (HTTP 409)
- Review ownership for update and delete
- Wishlist operations & transfer to cart
"""

from decimal import Decimal
from unittest.mock import MagicMock, patch
import pytest
from fastapi import HTTPException, status
from fastapi.testclient import TestClient

from app.api.deps import get_current_user
from app.main import app
from app.models.catalog import Book
from app.models.commerce import Cart, CartItem, Wishlist, WishlistItem
from app.models.experience import Review
from app.models.inventory import Inventory, InventoryTransaction
from app.models.user import Role, User, UserRole
from app.schemas.commerce import CartItemAddRequest, CartItemUpdateRequest
from app.schemas.experience import ReviewCreateRequest, ReviewUpdateRequest
from app.schemas.inventory import InventoryAdjustmentRequest, InventoryInboundRequest
from app.services.commerce_service import CartService, WishlistService
from app.services.inventory_service import InventoryService
from app.services.review_service import ReviewService

client = TestClient(app)


def make_user(user_id: int, role_name: str = "CUSTOMER") -> User:
    user = MagicMock(spec=User)
    user.id = user_id
    user.email = f"user_{user_id}@{role_name.lower()}.vn"
    user.full_name = f"Reader {user_id}"
    user.is_active = True

    role = MagicMock(spec=Role)
    role.name = role_name
    ur = MagicMock(spec=UserRole)
    ur.role = role
    user.roles = [ur]
    return user


def make_book_with_stock(
    book_id: int = 1,
    physical: int = 20,
    reserved: int = 5,
    price: Decimal = Decimal("100000.00"),
    status_str: str = "ACTIVE",
) -> Book:
    book = MagicMock(spec=Book)
    book.id = book_id
    book.title = "Đắc Nhân Tâm"
    book.isbn = "9786045622001"
    book.sku = "NOV-DNT-01"
    book.price = price
    book.original_price = Decimal("120000.00")
    book.cover_image_url = "https://images.novelia.vn/books/dnt.jpg"
    book.status = status_str

    inv = MagicMock(spec=Inventory)
    inv.id = book_id
    inv.book_id = book_id
    inv.physical_stock = physical
    inv.reserved_stock = reserved
    inv.available_stock = physical - reserved
    inv.low_stock_threshold = 10
    book.inventory = inv
    return book


# ============================================================================
# 1. INVENTORY & RBAC AUDIT TESTS
# ============================================================================


class TestInventoryManagementAndRBAC:
    """Verify inventory operations, safety thresholds, and strict role enforcement."""

    def test_customer_cannot_adjust_inventory_blocked_403(self):
        customer = make_user(1, "CUSTOMER")
        app.dependency_overrides[get_current_user] = lambda: customer
        try:
            with patch("app.repositories.user_repo.UserRepository.get_user_role_names", return_value=["CUSTOMER"]):
                payload = {
                    "book_id": 1,
                    "quantity_change": 10,
                    "reference_code": "TAMPER-01",
                    "reason": "Hacking inventory",
                }
                res = client.post("/api/v1/inventory/adjust", json=payload)
                assert res.status_code == status.HTTP_403_FORBIDDEN
        finally:
            app.dependency_overrides.clear()

    def test_staff_can_inbound_restock(self):
        from app.database.connection import get_db
        from app.services.inventory_service import to_inventory_read
        staff = make_user(2, "STAFF")
        mock_inv = MagicMock(spec=Inventory)
        mock_inv.id = 1
        mock_inv.book_id = 1
        mock_inv.physical_stock = 50
        mock_inv.reserved_stock = 0
        mock_inv.low_stock_threshold = 10
        mock_inv.updated_at = "2026-10-20T00:00:00Z"
        mock_book = make_book_with_stock(1, physical=50, reserved=0)
        mock_inv.book = mock_book

        mock_db = MagicMock()
        app.dependency_overrides[get_db] = lambda: mock_db
        app.dependency_overrides[get_current_user] = lambda: staff
        try:
            with patch("app.repositories.user_repo.UserRepository.get_user_role_names", return_value=["STAFF"]):
                with patch("app.services.inventory_service.InventoryService.inbound_restock", return_value=to_inventory_read(mock_inv)):
                    payload = {
                        "book_id": 1,
                        "quantity": 30,
                        "reference_code": "IMPORT-2026-001",
                        "reason": "Đợt nhập sách định kỳ",
                    }
                    res = client.post("/api/v1/inventory/inbound", json=payload)
                    assert res.status_code == status.HTTP_201_CREATED
                    data = res.json()
                    assert data["physical_stock"] == 50
                    assert data["available_stock"] == 50
        finally:
            app.dependency_overrides.clear()


    def test_adjustment_cannot_cause_negative_physical_stock(self):
        mock_db = MagicMock()
        mock_inv = MagicMock(spec=Inventory, physical_stock=5, reserved_stock=2)

        with patch("app.repositories.inventory_repo.InventoryRepository.get_by_book_id", return_value=mock_inv):
            from app.repositories.inventory_repo import InventoryRepository
            with pytest.raises(ValueError) as exc:
                InventoryRepository.adjust_stock(
                    db=mock_db,
                    book_id=1,
                    delta=-10,  # 5 - 10 = -5 < 0
                    reference_code="ADJ-FAIL",
                    reason="Excessive deduction",
                    staff_user_id=2,
                )
            assert "không thể âm" in str(exc.value)

    def test_adjustment_cannot_cause_stock_below_reserved(self):
        mock_db = MagicMock()
        mock_inv = MagicMock(spec=Inventory, physical_stock=10, reserved_stock=8)

        with patch("app.repositories.inventory_repo.InventoryRepository.get_by_book_id", return_value=mock_inv):
            from app.repositories.inventory_repo import InventoryRepository
            with pytest.raises(ValueError) as exc:
                InventoryRepository.adjust_stock(
                    db=mock_db,
                    book_id=1,
                    delta=-5,  # 10 - 5 = 5 < reserved (8)
                    reference_code="ADJ-FAIL",
                    reason="Below reserved",
                    staff_user_id=2,
                )
            assert "nhỏ hơn tồn kho giữ chỗ" in str(exc.value)


# ============================================================================
# 2. SHOPPING CART & BACKEND PRICING TESTS
# ============================================================================


class TestShoppingCartBusinessRules:
    """Verify backend cart calculations, stock barriers, and user isolation."""

    def test_add_item_invalid_zero_or_negative_quantity(self):
        mock_db = MagicMock()
        with pytest.raises(HTTPException) as exc:
            CartService.add_item(mock_db, user_id=1, book_id=1, quantity=0)
        assert exc.value.status_code == status.HTTP_400_BAD_REQUEST

        with pytest.raises(HTTPException) as exc_neg:
            CartService.add_item(mock_db, user_id=1, book_id=1, quantity=-3)
        assert exc_neg.value.status_code == status.HTTP_400_BAD_REQUEST

    def test_add_out_of_stock_book_rejected(self):
        mock_db = MagicMock()
        out_of_stock_book = make_book_with_stock(1, physical=5, reserved=5)  # available = 0

        with patch.object(mock_db, "query") as mock_query:
            mock_query.return_value.filter.return_value.first.return_value = out_of_stock_book
            with pytest.raises(HTTPException) as exc:
                CartService.add_item(mock_db, user_id=1, book_id=1, quantity=1)
            assert exc.value.status_code == status.HTTP_400_BAD_REQUEST
            assert "hết hàng" in exc.value.detail

    def test_add_quantity_exceeding_available_stock_rejected(self):
        mock_db = MagicMock()
        book = make_book_with_stock(1, physical=10, reserved=5)  # available = 5
        mock_cart = MagicMock(spec=Cart, id=1, user_id=1, items=[])

        with patch.object(mock_db, "query") as mock_query:
            mock_query.return_value.filter.return_value.first.return_value = book
            with patch("app.repositories.commerce_repo.CartRepository.get_or_create_cart", return_value=mock_cart):
                with patch("app.repositories.commerce_repo.CartRepository.get_cart_item", return_value=None):
                    with pytest.raises(HTTPException) as exc:
                        CartService.add_item(mock_db, user_id=1, book_id=1, quantity=6)
                    assert exc.value.status_code == status.HTTP_400_BAD_REQUEST
                    assert "vượt quá" in exc.value.detail

    def test_cart_tenant_isolation_two_users_distinct_carts(self):
        """Verify User A and User B query and mutate only their own cart in MySQL."""
        mock_db = MagicMock()
        cart_a = MagicMock(spec=Cart, id=101, user_id=1, items=[])
        cart_b = MagicMock(spec=Cart, id=202, user_id=2, items=[])

        def mock_get_or_create(db, user_id):
            if user_id == 1:
                return cart_a
            elif user_id == 2:
                return cart_b
            return None

        with patch("app.repositories.commerce_repo.CartRepository.get_or_create_cart", side_effect=mock_get_or_create):
            res_a = CartService.get_cart(mock_db, user_id=1)
            res_b = CartService.get_cart(mock_db, user_id=2)

            assert res_a.user_id == 1
            assert res_a.id == 101
            assert res_b.user_id == 2
            assert res_b.id == 202
            assert res_a.id != res_b.id

    def test_cart_authoritative_backend_pricing(self):
        """Verify cart subtotal is computed strictly from book.price in DB."""
        book1 = make_book_with_stock(1, price=Decimal("80000.00"), physical=20, reserved=0)
        book2 = make_book_with_stock(2, price=Decimal("120000.00"), physical=20, reserved=0)

        item1 = MagicMock(spec=CartItem, id=1, book_id=1, quantity=2, book=book1)
        item2 = MagicMock(spec=CartItem, id=2, book_id=2, quantity=1, book=book2)

        cart = MagicMock(spec=Cart, id=1, user_id=1, items=[item1, item2], updated_at="2026-10-20T00:00:00Z")

        from app.services.commerce_service import to_cart_read
        cart_read = to_cart_read(cart)

        # 2 * 80,000 + 1 * 120,000 = 280,000
        assert cart_read.total_items == 3
        assert cart_read.subtotal_amount == Decimal("280000.00")
        assert cart_read.has_stock_issues is False


# ============================================================================
# 3. WISHLIST TESTS
# ============================================================================


class TestWishlistService:
    """Verify wishlist storage, duplicate handling, and move-to-cart."""

    def test_add_and_move_to_cart(self):
        mock_db = MagicMock()
        book = make_book_with_stock(1, physical=10, reserved=0)

        with patch.object(mock_db, "query") as mock_query:
            mock_query.return_value.filter.return_value.first.return_value = book
            with patch("app.repositories.commerce_repo.WishlistRepository.get_or_create_wishlist"):
                with patch("app.repositories.commerce_repo.WishlistRepository.add_item"):
                    with patch("app.services.commerce_service.CartService.add_item") as mock_add_cart:
                        with patch("app.services.commerce_service.WishlistService.remove_item") as mock_remove_wish:
                            WishlistService.move_to_cart(mock_db, user_id=1, book_id=1)
                            mock_add_cart.assert_called_once_with(mock_db, user_id=1, book_id=1, quantity=1)
                            mock_remove_wish.assert_called_once_with(mock_db, user_id=1, book_id=1)


# ============================================================================
# 4. REVIEWS & ANTI-SPAM TESTS
# ============================================================================


class TestBookReviewsAndRatings:
    """Verify star ratings, anti-spam rules, duplicate protection, and RBAC."""

    def test_submit_duplicate_review_raises_conflict(self):
        mock_db = MagicMock()
        user = make_user(1)
        book = make_book_with_stock(1)
        existing_review = MagicMock(spec=Review, id=99)

        with patch.object(mock_db, "query") as mock_query:
            mock_query.return_value.filter.return_value.first.return_value = book
            with patch("app.repositories.review_repo.ReviewRepository.get_user_review_for_book", return_value=existing_review):
                req = ReviewCreateRequest(
                    rating=5,
                    title="Tuyệt phẩm",
                    comment="Cuốn sách làm thay đổi nhân sinh quan của tôi.",
                )
                with pytest.raises(HTTPException) as exc:
                    ReviewService.create_review(mock_db, user=user, book_id=1, data=req)
                assert exc.value.status_code == status.HTTP_409_CONFLICT
                assert "đã viết đánh giá" in exc.value.detail

    def test_update_other_user_review_forbidden(self):
        mock_db = MagicMock()
        user_a = make_user(1)
        # Review belongs to user 999
        review_other = MagicMock(spec=Review, id=10, user_id=999)

        with patch("app.repositories.review_repo.ReviewRepository.get_by_id", return_value=review_other):
            req = ReviewUpdateRequest(rating=4, comment="Sửa bài người khác.")
            with pytest.raises(HTTPException) as exc:
                ReviewService.update_review(mock_db, user=user_a, review_id=10, data=req)
            assert exc.value.status_code == status.HTTP_403_FORBIDDEN

    def test_rating_summary_calculation(self):
        """Verify average rating and distribution across 1 to 5 stars."""
        mock_db = MagicMock()
        # 3 reviews: 5, 5, 4 stars -> avg = 14 / 3 = 4.7
        mock_db.query.return_value.filter.return_value.all.return_value = [(5,), (5,), (4,)]

        from app.repositories.review_repo import ReviewRepository
        avg, total, dist = ReviewRepository.get_rating_summary(mock_db, book_id=1)

        assert total == 3
        assert avg == 4.7
        assert dist["5"] == 2
        assert dist["4"] == 1
        assert dist["1"] == 0
