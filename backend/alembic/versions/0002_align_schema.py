"""0002_align_schema: Align live database tables with NOVELIA BOOKS production domain models.

Reconciles column differences across:
- carts (adds created_at)
- cart_items (aligns added_at, adds updated_at)
- orders (aligns order_code, subtotal_amount, recipient_name, recipient_phone, shipping address fields)
- order_items (aligns book_title_snapshot, price_at_purchase, subtotal, snapshot metadata)
- books (fills missing SKUs)
- coupons (aligns max_discount_value, description, updated_at)
- payments (aligns payment_code, transaction_id, gateway_response, updated_at)
- shipments (aligns tracking_code, carrier, status, delivery metadata)
- reviews (adds title, updated_at)
- audit_logs (adds user_id, user_agent, old_values, new_values)

Revision ID: 0002_align_schema
Revises: 0001_initial_schema
Create Date: 2026-10-21
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "0002_align_schema"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)

    def get_col_names(table_name: str):
        return [c["name"] for c in insp.get_columns(table_name)]

    # 1. carts
    if "carts" in insp.get_table_names():
        cart_cols = get_col_names("carts")
        if "created_at" not in cart_cols:
            op.add_column("carts", sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")))

    # 2. cart_items
    if "cart_items" in insp.get_table_names():
        ci_cols = get_col_names("cart_items")
        if "added_at" not in ci_cols:
            if "created_at" in ci_cols:
                op.alter_column("cart_items", "created_at", new_column_name="added_at", type_=sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP"))
            else:
                op.add_column("cart_items", sa.Column("added_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")))
        ci_cols = get_col_names("cart_items")
        if "updated_at" not in ci_cols:
            op.add_column("cart_items", sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")))

    # 3. orders
    if "orders" in insp.get_table_names():
        o_cols = get_col_names("orders")
        if "order_code" not in o_cols and "order_number" in o_cols:
            op.alter_column("orders", "order_number", new_column_name="order_code", type_=sa.String(50), nullable=False)
        if "subtotal_amount" not in o_cols and "subtotal" in o_cols:
            op.alter_column("orders", "subtotal", new_column_name="subtotal_amount", type_=sa.DECIMAL(12, 2), nullable=False)
        if "recipient_name" not in o_cols and "receiver_name" in o_cols:
            op.alter_column("orders", "receiver_name", new_column_name="recipient_name", type_=sa.String(100), nullable=False)
        if "recipient_phone" not in o_cols and "receiver_phone" in o_cols:
            op.alter_column("orders", "receiver_phone", new_column_name="recipient_phone", type_=sa.String(20), nullable=False)
        if "shipping_street_address" not in o_cols and "shipping_address" in o_cols:
            op.alter_column("orders", "shipping_address", new_column_name="shipping_street_address", type_=sa.String(255), nullable=False)
        if "customer_notes" not in o_cols and "note" in o_cols:
            op.alter_column("orders", "note", new_column_name="customer_notes", type_=sa.Text(), nullable=True)

        o_cols = get_col_names("orders")
        if "shipping_province" not in o_cols:
            op.add_column("orders", sa.Column("shipping_province", sa.String(100), nullable=False, server_default="Hà Nội"))
        if "shipping_district" not in o_cols:
            op.add_column("orders", sa.Column("shipping_district", sa.String(100), nullable=False, server_default="Hoàn Kiếm"))
        if "shipping_ward" not in o_cols:
            op.add_column("orders", sa.Column("shipping_ward", sa.String(100), nullable=False, server_default="Hàng Bạc"))
        if "staff_notes" not in o_cols:
            op.add_column("orders", sa.Column("staff_notes", sa.Text(), nullable=True))
        if "cancelled_reason" not in o_cols:
            op.add_column("orders", sa.Column("cancelled_reason", sa.String(255), nullable=True))

    # 4. order_items
    if "order_items" in insp.get_table_names():
        oi_cols = get_col_names("order_items")
        if "book_title_snapshot" not in oi_cols and "book_title" in oi_cols:
            op.alter_column("order_items", "book_title", new_column_name="book_title_snapshot", type_=sa.String(255), nullable=False)
        if "price_at_purchase" not in oi_cols and "price" in oi_cols:
            op.alter_column("order_items", "price", new_column_name="price_at_purchase", type_=sa.DECIMAL(12, 2), nullable=False)
        if "subtotal" not in oi_cols and "total_price" in oi_cols:
            op.alter_column("order_items", "total_price", new_column_name="subtotal", type_=sa.DECIMAL(12, 2), nullable=False)

        oi_cols = get_col_names("order_items")
        if "book_isbn_snapshot" not in oi_cols:
            op.add_column("order_items", sa.Column("book_isbn_snapshot", sa.String(20), nullable=False, server_default=""))
        if "book_sku_snapshot" not in oi_cols:
            op.add_column("order_items", sa.Column("book_sku_snapshot", sa.String(50), nullable=False, server_default=""))
        if "created_at" not in oi_cols:
            op.add_column("order_items", sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")))

    # 5. books - fill null skus
    if "books" in insp.get_table_names():
        bind.execute(sa.text("UPDATE books SET sku = CONCAT('NOV-BK-', LPAD(id, 4, '0')) WHERE sku IS NULL OR sku = ''"))

    # 6. coupons
    if "coupons" in insp.get_table_names():
        cp_cols = get_col_names("coupons")
        if "max_discount_value" not in cp_cols and "max_discount_amount" in cp_cols:
            op.alter_column("coupons", "max_discount_amount", new_column_name="max_discount_value", type_=sa.DECIMAL(12, 2), nullable=True)
        cp_cols = get_col_names("coupons")
        if "description" not in cp_cols:
            op.add_column("coupons", sa.Column("description", sa.String(255), nullable=True))
        if "updated_at" not in cp_cols:
            op.add_column("coupons", sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")))

    # 7. payments
    if "payments" in insp.get_table_names():
        pm_cols = get_col_names("payments")
        if "payment_code" not in pm_cols and "transaction_code" in pm_cols:
            bind.execute(sa.text("UPDATE payments SET transaction_code = CONCAT('PAY-', LPAD(id, 6, '0')) WHERE transaction_code IS NULL OR transaction_code = ''"))
            op.alter_column("payments", "transaction_code", new_column_name="payment_code", type_=sa.String(50), nullable=False)
        pm_cols = get_col_names("payments")
        if "transaction_id" not in pm_cols:
            op.add_column("payments", sa.Column("transaction_id", sa.String(100), nullable=True))
        if "gateway_response" not in pm_cols:
            op.add_column("payments", sa.Column("gateway_response", sa.JSON(), nullable=True))
        if "updated_at" not in pm_cols:
            op.add_column("payments", sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")))

    # 8. shipments
    if "shipments" in insp.get_table_names():
        sh_cols = get_col_names("shipments")
        if "tracking_code" not in sh_cols and "tracking_number" in sh_cols:
            bind.execute(sa.text("UPDATE shipments SET tracking_number = CONCAT('TRK-', LPAD(id, 6, '0')) WHERE tracking_number IS NULL OR tracking_number = ''"))
            op.alter_column("shipments", "tracking_number", new_column_name="tracking_code", type_=sa.String(100), nullable=False)
        if "carrier" not in sh_cols and "shipping_carrier" in sh_cols:
            op.alter_column("shipments", "shipping_carrier", new_column_name="carrier", type_=sa.String(50), nullable=False)
        if "status" not in sh_cols and "shipping_status" in sh_cols:
            op.alter_column("shipments", "shipping_status", new_column_name="status", type_=sa.String(30), nullable=False, server_default="READY_FOR_PICKUP")
        sh_cols = get_col_names("shipments")
        if "shipping_service_id" not in sh_cols:
            op.add_column("shipments", sa.Column("shipping_service_id", sa.String(50), nullable=True))
        if "shipping_fee" not in sh_cols:
            op.add_column("shipments", sa.Column("shipping_fee", sa.DECIMAL(12, 2), nullable=False, server_default=sa.text("0.00")))
        if "estimated_delivery_date" not in sh_cols:
            if "estimated_delivery" in sh_cols:
                op.alter_column("shipments", "estimated_delivery", new_column_name="estimated_delivery_date", type_=sa.DateTime(), nullable=True)
            else:
                op.add_column("shipments", sa.Column("estimated_delivery_date", sa.DateTime(), nullable=True))
        if "delivered_at" not in sh_cols:
            if "actual_delivery" in sh_cols:
                op.alter_column("shipments", "actual_delivery", new_column_name="delivered_at", type_=sa.DateTime(), nullable=True)
            else:
                op.add_column("shipments", sa.Column("delivered_at", sa.DateTime(), nullable=True))
        if "dispatched_at" not in sh_cols:
            op.add_column("shipments", sa.Column("dispatched_at", sa.DateTime(), nullable=True))

    # 9. reviews
    if "reviews" in insp.get_table_names():
        rv_cols = get_col_names("reviews")
        if "title" not in rv_cols:
            op.add_column("reviews", sa.Column("title", sa.String(150), nullable=True))
        if "updated_at" not in rv_cols:
            op.add_column("reviews", sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP")))

    # 10. audit_logs
    if "audit_logs" in insp.get_table_names():
        al_cols = get_col_names("audit_logs")
        if "user_id" not in al_cols:
            op.add_column("audit_logs", sa.Column("user_id", sa.BigInteger(), nullable=True))
        if "user_agent" not in al_cols:
            op.add_column("audit_logs", sa.Column("user_agent", sa.String(255), nullable=True))
        if "old_values" not in al_cols:
            op.add_column("audit_logs", sa.Column("old_values", sa.JSON(), nullable=True))
        if "new_values" not in al_cols:
            op.add_column("audit_logs", sa.Column("new_values", sa.JSON(), nullable=True))


def downgrade() -> None:
    pass
