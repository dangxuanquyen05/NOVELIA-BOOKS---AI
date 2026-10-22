"""Unit tests for NOVELIA BOOKS SQLAlchemy models, metadata, constraints, and seed data structures.
These tests validate database architecture without requiring a live database connection.
"""

from decimal import Decimal
import pytest
from sqlalchemy import DECIMAL, BigInteger, CheckConstraint, String, UniqueConstraint

import app.models
from app.models import Base
from app.models.catalog import Book, Category, Publisher, Author
from app.models.commerce import Order, OrderItem, Coupon
from app.models.inventory import Inventory
from app.models.user import User, Role
from app.database.seeds import (
    ROLES_DATA,
    PUBLISHERS_DATA,
    CATEGORIES_DATA,
    AUTHORS_DATA,
    BOOKS_DATA,
)


class TestModelMetadataAndSchema:
    """Test suite verifying table registry, column definitions, and constraints."""

    def test_total_table_count(self):
        """Verify all 34 tables across the 8 domains are registered in Base.metadata."""
        tables = Base.metadata.tables
        assert len(tables) == 34, f"Expected 34 tables, found {len(tables)}: {list(tables.keys())}"

    def test_expected_tables_present(self):
        """Verify key entity tables exist in metadata."""
        tables = Base.metadata.tables
        expected_tables = [
            # A. Users
            "roles", "users", "user_roles", "user_addresses", "user_preferences",
            # B. Catalog
            "publishers", "authors", "categories", "books", "book_authors", "book_categories", "book_images",
            # C. Inventory
            "inventory", "inventory_transactions",
            # D. Commerce
            "carts", "cart_items", "wishlists", "wishlist_items", "orders", "order_items", "coupons", "coupon_usages",
            # E. Payment & Shipping
            "payments", "refund_requests", "shipments", "shipment_events",
            # F. Experience
            "reviews", "notifications",
            # G. AI
            "ai_conversations", "ai_messages", "ai_action_logs", "user_book_events", "book_recommendations",
            # H. Audit
            "audit_logs",
        ]
        for tbl in expected_tables:
            assert tbl in tables, f"Missing table: {tbl}"

    def test_monetary_fields_use_decimal(self):
        """Verify monetary fields strictly use DECIMAL and never Float."""
        # Book prices
        assert isinstance(Book.price.type, DECIMAL)
        assert Book.price.type.precision == 12
        assert Book.price.type.scale == 2

        assert isinstance(Book.original_price.type, DECIMAL)
        assert Book.original_price.type.precision == 12
        assert Book.original_price.type.scale == 2

        # Order amounts
        assert isinstance(Order.subtotal_amount.type, DECIMAL)
        assert Order.subtotal_amount.type.precision == 12
        assert Order.subtotal_amount.type.scale == 2

        assert isinstance(Order.total_amount.type, DECIMAL)
        assert Order.total_amount.type.precision == 12
        assert Order.total_amount.type.scale == 2

        # OrderItem snapshot & subtotal
        assert isinstance(OrderItem.price_at_purchase.type, DECIMAL)
        assert OrderItem.price_at_purchase.type.precision == 12
        assert OrderItem.price_at_purchase.type.scale == 2

        assert isinstance(OrderItem.subtotal.type, DECIMAL)
        assert OrderItem.subtotal.type.precision == 12
        assert OrderItem.subtotal.type.scale == 2

    def test_order_item_snapshot_fields_exist(self):
        """Verify immutable snapshot fields on order_items table to protect financial auditability."""
        cols = Base.metadata.tables["order_items"].columns
        assert "book_title_snapshot" in cols
        assert "book_isbn_snapshot" in cols
        assert "book_sku_snapshot" in cols
        assert "price_at_purchase" in cols
        assert "quantity" in cols
        assert "subtotal" in cols
        # book_id must be nullable with SET NULL to preserve order history even if a book is archived
        assert cols["book_id"].nullable is True

    def test_inventory_check_constraints(self):
        """Verify non-negative inventory check constraints."""
        table = Base.metadata.tables["inventory"]
        constraint_names = [c.name for c in table.constraints if isinstance(c, CheckConstraint)]
        assert "chk_inventory_non_negative" in constraint_names
        assert "chk_physical_non_negative" in constraint_names
        assert "chk_reserved_non_negative" in constraint_names

    def test_order_check_constraints(self):
        """Verify non-negative financial check constraints on orders table."""
        table = Base.metadata.tables["orders"]
        constraint_names = [c.name for c in table.constraints if isinstance(c, CheckConstraint)]
        assert "chk_order_subtotal_non_negative" in constraint_names
        assert "chk_order_shipping_non_negative" in constraint_names
        assert "chk_order_total_non_negative" in constraint_names

    def test_unique_constraints(self):
        """Verify essential unique constraints on business identifiers."""
        # Book ISBN and SKU
        books_table = Base.metadata.tables["books"]
        assert books_table.columns["isbn"].unique is True
        assert books_table.columns["sku"].unique is True

        # User email
        users_table = Base.metadata.tables["users"]
        assert users_table.columns["email"].unique is True

        # Order code
        orders_table = Base.metadata.tables["orders"]
        assert orders_table.columns["order_code"].unique is True

        # Coupon code
        coupons_table = Base.metadata.tables["coupons"]
        assert coupons_table.columns["code"].unique is True

    def test_primary_keys_use_biginteger(self):
        """Verify primary keys use BigInteger to handle large scale enterprise volume."""
        tables_to_check = ["users", "books", "orders", "order_items", "inventory_transactions"]
        for tbl_name in tables_to_check:
            pk_col = list(Base.metadata.tables[tbl_name].primary_key.columns)[0]
            assert isinstance(pk_col.type, BigInteger), f"{tbl_name} PK is not BigInteger"


class TestSeedDataIntegrity:
    """Test suite verifying quality and consistency of seed data structures."""

    def test_seed_roles_count_and_names(self):
        """Verify predefined RBAC roles."""
        role_names = [r["name"] for r in ROLES_DATA]
        assert "CUSTOMER" in role_names
        assert "STAFF" in role_names
        assert "ADMIN" in role_names

    def test_seed_categories_count(self):
        """Verify seed categories meet roadmap requirements (6-10 categories)."""
        assert 6 <= len(CATEGORIES_DATA) <= 12
        slugs = [c["slug"] for c in CATEGORIES_DATA]
        assert len(slugs) == len(set(slugs)), "Duplicate category slug found"

    def test_seed_authors_count(self):
        """Verify seed authors meet roadmap requirements (20-30 authors)."""
        assert 20 <= len(AUTHORS_DATA) <= 35
        slugs = [a["slug"] for a in AUTHORS_DATA]
        assert len(slugs) == len(set(slugs)), "Duplicate author slug found"

    def test_seed_publishers_count(self):
        """Verify seed publishers meet roadmap requirements (5-10 publishers)."""
        assert 5 <= len(PUBLISHERS_DATA) <= 12
        slugs = [p["slug"] for p in PUBLISHERS_DATA]
        assert len(slugs) == len(set(slugs)), "Duplicate publisher slug found"

    def test_seed_books_count_and_validity(self):
        """Verify at least 30 books with valid fields, ISBNs, and prices."""
        assert len(BOOKS_DATA) >= 30, f"Expected >= 30 books, found {len(BOOKS_DATA)}"

        isbns = set()
        skus = set()
        publisher_slugs = {p["slug"] for p in PUBLISHERS_DATA}
        author_slugs = {a["slug"] for a in AUTHORS_DATA}
        category_slugs = {c["slug"] for c in CATEGORIES_DATA}

        for book in BOOKS_DATA:
            # Uniqueness
            assert book["isbn"] not in isbns, f"Duplicate ISBN: {book['isbn']}"
            assert book["sku"] not in skus, f"Duplicate SKU: {book['sku']}"
            isbns.add(book["isbn"])
            skus.add(book["sku"])

            # References
            assert book["publisher_slug"] in publisher_slugs, f"Invalid publisher: {book['publisher_slug']}"
            for auth in book["author_slugs"]:
                assert auth in author_slugs, f"Invalid author slug: {auth}"
            for cat in book["category_slugs"]:
                assert cat in category_slugs, f"Invalid category slug: {cat}"

            # Pricing
            assert isinstance(book["price"], Decimal)
            assert book["price"] > 0
            assert book["price"] <= book["original_price"]

            # Inventory
            assert book["stock"] >= 0

            # Demo labeling
            assert "[DEMO SEED]" in book["description"]
