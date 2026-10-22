"""0001_initial_schema: Initial database schema for NOVELIA BOOKS.

Creates all 34 relational tables across the 8 functional domains:
- USERS & ACCESS (roles, users, user_roles, user_addresses, user_preferences)
- CATALOG (publishers, authors, categories, books, book_authors, book_categories, book_images)
- INVENTORY (inventory, inventory_transactions)
- COMMERCE (carts, cart_items, wishlists, wishlist_items, orders, order_items, coupons, coupon_usages)
- PAYMENT & SHIPPING (payments, refund_requests, shipments, shipment_events)
- CUSTOMER EXPERIENCE (reviews, notifications)
- AI ECOSYSTEM (ai_conversations, ai_messages, ai_action_logs, user_book_events, book_recommendations)
- SYSTEM AUDITING (audit_logs)

Revision ID: 0001_initial_schema
Revises: None
Create Date: 2026-10-20
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ---------------------------------------------------------
    # 1. USERS & ACCESS
    # ---------------------------------------------------------
    op.create_table(
        "roles",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
    )
    op.create_index("ix_roles_name", "roles", ["name"], unique=True)

    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=150), nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "user_roles",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("role_id", sa.BigInteger(), nullable=False),
        sa.Column("assigned_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["role_id"], ["roles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "role_id", name="uq_user_role"),
    )
    op.create_index("idx_user_roles_user", "user_roles", ["user_id"])
    op.create_index("idx_user_roles_role", "user_roles", ["role_id"])

    op.create_table(
        "user_addresses",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("recipient_name", sa.String(length=100), nullable=False),
        sa.Column("phone", sa.String(length=20), nullable=False),
        sa.Column("province_code", sa.String(length=50), nullable=False),
        sa.Column("province_name", sa.String(length=100), nullable=False),
        sa.Column("district_code", sa.String(length=50), nullable=False),
        sa.Column("district_name", sa.String(length=100), nullable=False),
        sa.Column("ward_code", sa.String(length=50), nullable=False),
        sa.Column("ward_name", sa.String(length=100), nullable=False),
        sa.Column("street_address", sa.String(length=255), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_user_addresses_user", "user_addresses", ["user_id"])

    op.create_table(
        "user_preferences",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("preferred_categories", sa.JSON(), nullable=False),
        sa.Column("preferred_authors", sa.JSON(), nullable=True),
        sa.Column("reading_goals", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )

    # ---------------------------------------------------------
    # 2. CATALOG
    # ---------------------------------------------------------
    op.create_table(
        "publishers",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("slug", sa.String(length=170), nullable=False),
        sa.Column("contact_info", sa.String(length=255), nullable=True),
        sa.Column("address", sa.String(length=255), nullable=True),
        sa.Column("website", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("ix_publishers_name", "publishers", ["name"], unique=True)
    op.create_index("ix_publishers_slug", "publishers", ["slug"], unique=True)

    op.create_table(
        "authors",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=150), nullable=False),
        sa.Column("slug", sa.String(length=170), nullable=False),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("avatar_url", sa.String(length=500), nullable=True),
        sa.Column("birth_year", sa.Integer(), nullable=True),
        sa.Column("nationality", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("ix_authors_name", "authors", ["name"])
    op.create_index("ix_authors_slug", "authors", ["slug"], unique=True)

    op.create_table(
        "categories",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("slug", sa.String(length=120), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("parent_id", sa.BigInteger(), nullable=True),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["parent_id"], ["categories.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("ix_categories_name", "categories", ["name"], unique=True)
    op.create_index("ix_categories_slug", "categories", ["slug"], unique=True)

    op.create_table(
        "books",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("isbn", sa.String(length=20), nullable=False),
        sa.Column("sku", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=280), nullable=False),
        sa.Column("publisher_id", sa.BigInteger(), nullable=False),
        sa.Column("price", sa.DECIMAL(precision=12, scale=2), nullable=False),
        sa.Column("original_price", sa.DECIMAL(precision=12, scale=2), nullable=False),
        sa.Column("page_count", sa.Integer(), nullable=True),
        sa.Column("dimension", sa.String(length=50), nullable=True),
        sa.Column("weight_grams", sa.Integer(), nullable=False, server_default=sa.text("300")),
        sa.Column("cover_type", sa.String(length=30), nullable=False, server_default="PAPERBACK"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("sample_text", sa.Text(), nullable=True),
        sa.Column("cover_image_url", sa.String(length=500), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="ACTIVE"),
        sa.Column("published_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["publisher_id"], ["publishers.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("isbn"),
        sa.UniqueConstraint("sku"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index("ix_books_isbn", "books", ["isbn"], unique=True)
    op.create_index("ix_books_sku", "books", ["sku"], unique=True)
    op.create_index("ix_books_slug", "books", ["slug"], unique=True)
    op.create_index("ix_books_title", "books", ["title"])
    op.create_index("idx_books_publisher", "books", ["publisher_id"])
    op.create_index("idx_books_status", "books", ["status"])
    op.create_index("idx_books_price", "books", ["price"])

    op.create_table(
        "book_authors",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("book_id", sa.BigInteger(), nullable=False),
        sa.Column("author_id", sa.BigInteger(), nullable=False),
        sa.Column("is_primary", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.ForeignKeyConstraint(["author_id"], ["authors.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["book_id"], ["books.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("book_id", "author_id", name="uq_book_author"),
    )
    op.create_index("idx_book_authors_book", "book_authors", ["book_id"])
    op.create_index("idx_book_authors_author", "book_authors", ["author_id"])

    op.create_table(
        "book_categories",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("book_id", sa.BigInteger(), nullable=False),
        sa.Column("category_id", sa.BigInteger(), nullable=False),
        sa.ForeignKeyConstraint(["book_id"], ["books.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("book_id", "category_id", name="uq_book_category"),
    )
    op.create_index("idx_book_categories_book", "book_categories", ["book_id"])
    op.create_index("idx_book_categories_category", "book_categories", ["category_id"])

    op.create_table(
        "book_images",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("book_id", sa.BigInteger(), nullable=False),
        sa.Column("image_url", sa.String(length=500), nullable=False),
        sa.Column("alt_text", sa.String(length=255), nullable=True),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("is_cover", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["book_id"], ["books.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_book_images_book", "book_images", ["book_id"])

    # ---------------------------------------------------------
    # 3. INVENTORY
    # ---------------------------------------------------------
    op.create_table(
        "inventory",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("book_id", sa.BigInteger(), nullable=False),
        sa.Column("physical_stock", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("reserved_stock", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("low_stock_threshold", sa.Integer(), nullable=False, server_default=sa.text("10")),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("physical_stock >= reserved_stock", name="chk_inventory_non_negative"),
        sa.CheckConstraint("physical_stock >= 0", name="chk_physical_non_negative"),
        sa.CheckConstraint("reserved_stock >= 0", name="chk_reserved_non_negative"),
        sa.ForeignKeyConstraint(["book_id"], ["books.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("book_id"),
    )
    op.create_index("idx_inventory_book", "inventory", ["book_id"])

    op.create_table(
        "inventory_transactions",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("inventory_id", sa.BigInteger(), nullable=False),
        sa.Column("transaction_type", sa.String(length=50), nullable=False),
        sa.Column("quantity_change", sa.Integer(), nullable=False),
        sa.Column("stock_after", sa.Integer(), nullable=False),
        sa.Column("reference_code", sa.String(length=100), nullable=True),
        sa.Column("notes", sa.String(length=255), nullable=True),
        sa.Column("created_by_user_id", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["inventory_id"], ["inventory.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_inv_trans_inventory", "inventory_transactions", ["inventory_id"])
    op.create_index("idx_inv_trans_created_at", "inventory_transactions", ["created_at"])
    op.create_index("ix_inventory_transactions_transaction_type", "inventory_transactions", ["transaction_type"])
    op.create_index("ix_inventory_transactions_reference_code", "inventory_transactions", ["reference_code"])

    # ---------------------------------------------------------
    # 4. COMMERCE
    # ---------------------------------------------------------
    op.create_table(
        "carts",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index("idx_carts_user", "carts", ["user_id"])

    op.create_table(
        "cart_items",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("cart_id", sa.BigInteger(), nullable=False),
        sa.Column("book_id", sa.BigInteger(), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("added_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("quantity > 0", name="chk_cart_item_quantity_positive"),
        sa.ForeignKeyConstraint(["book_id"], ["books.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["cart_id"], ["carts.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("cart_id", "book_id", name="uq_cart_book"),
    )
    op.create_index("idx_cart_items_cart", "cart_items", ["cart_id"])
    op.create_index("idx_cart_items_book", "cart_items", ["book_id"])

    op.create_table(
        "wishlists",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False, server_default="My Wishlist"),
        sa.Column("is_public", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_wishlists_user", "wishlists", ["user_id"])

    op.create_table(
        "wishlist_items",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("wishlist_id", sa.BigInteger(), nullable=False),
        sa.Column("book_id", sa.BigInteger(), nullable=False),
        sa.Column("added_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["book_id"], ["books.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["wishlist_id"], ["wishlists.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("wishlist_id", "book_id", name="uq_wishlist_book"),
    )
    op.create_index("idx_wishlist_items_wishlist", "wishlist_items", ["wishlist_id"])
    op.create_index("idx_wishlist_items_book", "wishlist_items", ["book_id"])

    op.create_table(
        "orders",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("order_code", sa.String(length=50), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("subtotal_amount", sa.DECIMAL(precision=12, scale=2), nullable=False),
        sa.Column("shipping_fee", sa.DECIMAL(precision=12, scale=2), nullable=False, server_default=sa.text("0.00")),
        sa.Column("discount_amount", sa.DECIMAL(precision=12, scale=2), nullable=False, server_default=sa.text("0.00")),
        sa.Column("total_amount", sa.DECIMAL(precision=12, scale=2), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="PENDING"),
        sa.Column("recipient_name", sa.String(length=100), nullable=False),
        sa.Column("recipient_phone", sa.String(length=20), nullable=False),
        sa.Column("shipping_province", sa.String(length=100), nullable=False),
        sa.Column("shipping_district", sa.String(length=100), nullable=False),
        sa.Column("shipping_ward", sa.String(length=100), nullable=False),
        sa.Column("shipping_street_address", sa.String(length=255), nullable=False),
        sa.Column("customer_notes", sa.Text(), nullable=True),
        sa.Column("staff_notes", sa.Text(), nullable=True),
        sa.Column("cancelled_reason", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("subtotal_amount >= 0", name="chk_order_subtotal_non_negative"),
        sa.CheckConstraint("shipping_fee >= 0", name="chk_order_shipping_non_negative"),
        sa.CheckConstraint("discount_amount >= 0", name="chk_order_discount_non_negative"),
        sa.CheckConstraint("total_amount >= 0", name="chk_order_total_non_negative"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("order_code"),
    )
    op.create_index("ix_orders_order_code", "orders", ["order_code"], unique=True)
    op.create_index("idx_orders_user", "orders", ["user_id"])
    op.create_index("idx_orders_status", "orders", ["status"])
    op.create_index("idx_orders_created_at", "orders", ["created_at"])

    op.create_table(
        "order_items",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("order_id", sa.BigInteger(), nullable=False),
        sa.Column("book_id", sa.BigInteger(), nullable=True),
        sa.Column("book_title_snapshot", sa.String(length=255), nullable=False),
        sa.Column("book_isbn_snapshot", sa.String(length=20), nullable=False),
        sa.Column("book_sku_snapshot", sa.String(length=50), nullable=False),
        sa.Column("price_at_purchase", sa.DECIMAL(precision=12, scale=2), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("subtotal", sa.DECIMAL(precision=12, scale=2), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("quantity > 0", name="chk_order_item_quantity_positive"),
        sa.CheckConstraint("price_at_purchase >= 0", name="chk_order_item_price_non_negative"),
        sa.CheckConstraint("subtotal >= 0", name="chk_order_item_subtotal_non_negative"),
        sa.ForeignKeyConstraint(["book_id"], ["books.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_order_items_order", "order_items", ["order_id"])
    op.create_index("idx_order_items_book", "order_items", ["book_id"])

    op.create_table(
        "coupons",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("discount_type", sa.String(length=20), nullable=False),
        sa.Column("discount_value", sa.DECIMAL(precision=12, scale=2), nullable=False),
        sa.Column("min_order_value", sa.DECIMAL(precision=12, scale=2), nullable=False, server_default=sa.text("0.00")),
        sa.Column("max_discount_value", sa.DECIMAL(precision=12, scale=2), nullable=True),
        sa.Column("usage_limit", sa.Integer(), nullable=True),
        sa.Column("used_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("start_date", sa.DateTime(), nullable=False),
        sa.Column("end_date", sa.DateTime(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("discount_value > 0", name="chk_coupon_discount_value_positive"),
        sa.CheckConstraint("min_order_value >= 0", name="chk_coupon_min_order_non_negative"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_index("ix_coupons_code", "coupons", ["code"], unique=True)
    op.create_index("idx_coupons_active_dates", "coupons", ["is_active", "start_date", "end_date"])

    op.create_table(
        "coupon_usages",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("coupon_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("order_id", sa.BigInteger(), nullable=False),
        sa.Column("discount_applied", sa.DECIMAL(precision=12, scale=2), nullable=False),
        sa.Column("used_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["coupon_id"], ["coupons.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("coupon_id", "order_id", name="uq_coupon_order"),
    )
    op.create_index("idx_coupon_usages_coupon", "coupon_usages", ["coupon_id"])
    op.create_index("idx_coupon_usages_user", "coupon_usages", ["user_id"])
    op.create_index("idx_coupon_usages_order", "coupon_usages", ["order_id"])

    # ---------------------------------------------------------
    # 5. PAYMENT & SHIPPING
    # ---------------------------------------------------------
    op.create_table(
        "payments",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("payment_code", sa.String(length=50), nullable=False),
        sa.Column("order_id", sa.BigInteger(), nullable=False),
        sa.Column("payment_method", sa.String(length=30), nullable=False),
        sa.Column("payment_status", sa.String(length=30), nullable=False, server_default="PENDING"),
        sa.Column("amount", sa.DECIMAL(precision=12, scale=2), nullable=False),
        sa.Column("transaction_id", sa.String(length=100), nullable=True),
        sa.Column("gateway_response", sa.JSON(), nullable=True),
        sa.Column("paid_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("amount >= 0", name="chk_payment_amount_non_negative"),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("order_id"),
        sa.UniqueConstraint("payment_code"),
    )
    op.create_index("ix_payments_payment_code", "payments", ["payment_code"], unique=True)
    op.create_index("idx_payments_order", "payments", ["order_id"])
    op.create_index("idx_payments_status", "payments", ["payment_status"])
    op.create_index("idx_payments_method", "payments", ["payment_method"])
    op.create_index("ix_payments_transaction_id", "payments", ["transaction_id"])

    op.create_table(
        "refund_requests",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("refund_code", sa.String(length=50), nullable=False),
        sa.Column("order_id", sa.BigInteger(), nullable=False),
        sa.Column("payment_id", sa.BigInteger(), nullable=True),
        sa.Column("amount", sa.DECIMAL(precision=12, scale=2), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="PENDING"),
        sa.Column("admin_notes", sa.Text(), nullable=True),
        sa.Column("processed_by_user_id", sa.BigInteger(), nullable=True),
        sa.Column("processed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("amount > 0", name="chk_refund_amount_positive"),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["payment_id"], ["payments.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["processed_by_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("refund_code"),
    )
    op.create_index("ix_refund_requests_refund_code", "refund_requests", ["refund_code"], unique=True)
    op.create_index("idx_refunds_order", "refund_requests", ["order_id"])
    op.create_index("idx_refunds_status", "refund_requests", ["status"])

    op.create_table(
        "shipments",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("tracking_code", sa.String(length=100), nullable=True),
        sa.Column("order_id", sa.BigInteger(), nullable=False),
        sa.Column("carrier", sa.String(length=50), nullable=False),
        sa.Column("shipping_service_id", sa.String(length=50), nullable=True),
        sa.Column("shipping_fee", sa.DECIMAL(precision=12, scale=2), nullable=False, server_default=sa.text("0.00")),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="PENDING"),
        sa.Column("estimated_delivery_date", sa.Date(), nullable=True),
        sa.Column("dispatched_at", sa.DateTime(), nullable=True),
        sa.Column("delivered_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("shipping_fee >= 0", name="chk_shipment_fee_non_negative"),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("order_id"),
        sa.UniqueConstraint("tracking_code"),
    )
    op.create_index("ix_shipments_tracking_code", "shipments", ["tracking_code"], unique=True)
    op.create_index("idx_shipments_order", "shipments", ["order_id"])
    op.create_index("idx_shipments_status", "shipments", ["status"])
    op.create_index("idx_shipments_carrier", "shipments", ["carrier"])

    op.create_table(
        "shipment_events",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("shipment_id", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("description", sa.String(length=255), nullable=False),
        sa.Column("raw_payload", sa.JSON(), nullable=True),
        sa.Column("occurred_at", sa.DateTime(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["shipment_id"], ["shipments.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_shipment_events_shipment", "shipment_events", ["shipment_id"])
    op.create_index("idx_shipment_events_occurred", "shipment_events", ["occurred_at"])

    # ---------------------------------------------------------
    # 6. CUSTOMER EXPERIENCE
    # ---------------------------------------------------------
    op.create_table(
        "reviews",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("book_id", sa.BigInteger(), nullable=False),
        sa.Column("order_id", sa.BigInteger(), nullable=True),
        sa.Column("rating", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=150), nullable=True),
        sa.Column("comment", sa.Text(), nullable=False),
        sa.Column("is_verified_purchase", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="APPROVED"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("rating >= 1 AND rating <= 5", name="chk_review_rating_1_to_5"),
        sa.ForeignKeyConstraint(["book_id"], ["books.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["order_id"], ["orders.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "book_id", name="uq_user_book_review"),
    )
    op.create_index("idx_reviews_book", "reviews", ["book_id"])
    op.create_index("idx_reviews_user", "reviews", ["user_id"])
    op.create_index("idx_reviews_rating", "reviews", ["rating"])
    op.create_index("idx_reviews_status", "reviews", ["status"])

    op.create_table(
        "notifications",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("title", sa.String(length=150), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("notification_type", sa.String(length=50), nullable=False),
        sa.Column("reference_link", sa.String(length=255), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("read_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_notifications_notification_type", "notifications", ["notification_type"])
    op.create_index("idx_notifications_user_read", "notifications", ["user_id", "is_read"])
    op.create_index("idx_notifications_created", "notifications", ["created_at"])

    # ---------------------------------------------------------
    # 7. AI ECOSYSTEM
    # ---------------------------------------------------------
    op.create_table(
        "ai_conversations",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("session_uuid", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=True),
        sa.Column("conversation_type", sa.String(length=50), nullable=False, server_default="ASSISTANT"),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("session_uuid"),
    )
    op.create_index("ix_ai_conversations_session_uuid", "ai_conversations", ["session_uuid"], unique=True)
    op.create_index("idx_ai_conversations_user", "ai_conversations", ["user_id"])
    op.create_index("idx_ai_conversations_created", "ai_conversations", ["created_at"])

    op.create_table(
        "ai_messages",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("conversation_id", sa.BigInteger(), nullable=False),
        sa.Column("sender", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("tool_calls", sa.JSON(), nullable=True),
        sa.Column("tool_results", sa.JSON(), nullable=True),
        sa.Column("tokens_used", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["conversation_id"], ["ai_conversations.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_ai_messages_conv", "ai_messages", ["conversation_id"])
    op.create_index("idx_ai_messages_created", "ai_messages", ["created_at"])

    op.create_table(
        "ai_action_logs",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("conversation_id", sa.BigInteger(), nullable=True),
        sa.Column("user_id", sa.BigInteger(), nullable=True),
        sa.Column("user_role", sa.String(length=50), nullable=False),
        sa.Column("tool_name", sa.String(length=100), nullable=False),
        sa.Column("input_arguments", sa.JSON(), nullable=False),
        sa.Column("execution_status", sa.String(length=50), nullable=False),
        sa.Column("confirmation_token", sa.String(length=100), nullable=True),
        sa.Column("is_confirmed", sa.Boolean(), nullable=False, server_default=sa.text("0")),
        sa.Column("output_summary", sa.Text(), nullable=True),
        sa.Column("execution_duration_ms", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["conversation_id"], ["ai_conversations.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_ai_actions_user", "ai_action_logs", ["user_id"])
    op.create_index("idx_ai_actions_tool", "ai_action_logs", ["tool_name"])
    op.create_index("idx_ai_actions_status", "ai_action_logs", ["execution_status"])
    op.create_index("idx_ai_actions_token", "ai_action_logs", ["confirmation_token"])

    op.create_table(
        "user_book_events",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=True),
        sa.Column("session_id", sa.String(length=100), nullable=True),
        sa.Column("book_id", sa.BigInteger(), nullable=False),
        sa.Column("event_type", sa.String(length=50), nullable=False),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["book_id"], ["books.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_events_user", "user_book_events", ["user_id"])
    op.create_index("idx_events_book", "user_book_events", ["book_id"])
    op.create_index("idx_events_type_created", "user_book_events", ["event_type", "created_at"])
    op.create_index("ix_user_book_events_session_id", "user_book_events", ["session_id"])

    op.create_table(
        "book_recommendations",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("book_id", sa.BigInteger(), nullable=False),
        sa.Column("algorithm_type", sa.String(length=50), nullable=False),
        sa.Column("score", sa.DECIMAL(precision=5, scale=4), nullable=False),
        sa.Column("reason", sa.String(length=255), nullable=True),
        sa.Column("generated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("score >= 0.0000 AND score <= 1.0000", name="chk_rec_score_range"),
        sa.ForeignKeyConstraint(["book_id"], ["books.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "book_id", "algorithm_type", name="uq_user_book_rec"),
    )
    op.create_index("idx_recs_user", "book_recommendations", ["user_id"])
    op.create_index("idx_recs_algo_score", "book_recommendations", ["algorithm_type", "score"])

    # ---------------------------------------------------------
    # 8. SYSTEM AUDITING
    # ---------------------------------------------------------
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=True),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("entity_type", sa.String(length=100), nullable=False),
        sa.Column("entity_id", sa.String(length=100), nullable=True),
        sa.Column("old_values", sa.JSON(), nullable=True),
        sa.Column("new_values", sa.JSON(), nullable=True),
        sa.Column("ip_address", sa.String(length=45), nullable=True),
        sa.Column("user_agent", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("idx_audit_user", "audit_logs", ["user_id"])
    op.create_index("idx_audit_entity", "audit_logs", ["entity_type", "entity_id"])
    op.create_index("idx_audit_created", "audit_logs", ["created_at"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])


def downgrade() -> None:
    # Drop tables in reverse topological order of foreign key dependencies
    op.drop_table("audit_logs")
    op.drop_table("book_recommendations")
    op.drop_table("user_book_events")
    op.drop_table("ai_action_logs")
    op.drop_table("ai_messages")
    op.drop_table("ai_conversations")
    op.drop_table("notifications")
    op.drop_table("reviews")
    op.drop_table("shipment_events")
    op.drop_table("shipments")
    op.drop_table("refund_requests")
    op.drop_table("payments")
    op.drop_table("coupon_usages")
    op.drop_table("coupons")
    op.drop_table("order_items")
    op.drop_table("orders")
    op.drop_table("wishlist_items")
    op.drop_table("wishlists")
    op.drop_table("cart_items")
    op.drop_table("carts")
    op.drop_table("inventory_transactions")
    op.drop_table("inventory")
    op.drop_table("book_images")
    op.drop_table("book_categories")
    op.drop_table("book_authors")
    op.drop_table("books")
    op.drop_table("categories")
    op.drop_table("authors")
    op.drop_table("publishers")
    op.drop_table("user_preferences")
    op.drop_table("user_addresses")
    op.drop_table("user_roles")
    op.drop_table("users")
    op.drop_table("roles")
