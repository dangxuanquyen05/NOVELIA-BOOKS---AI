"""0003_smart_address_fields: Add geolocation, place ID, and normalized address fields.

Adds:
- user_addresses: formatted_address, latitude, longitude, place_id, source_provider, confidence
- orders: shipping_formatted_address, shipping_latitude, shipping_longitude

Revision ID: 0003_smart_address_fields
Revises: 0002_align_schema
Create Date: 2026-10-22
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

revision = "0003_smart_address_fields"
down_revision = "0002_align_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)

    def get_col_names(table_name: str):
        if table_name in insp.get_table_names():
            return [c["name"] for c in insp.get_columns(table_name)]
        return []

    # 1. user_addresses
    addr_cols = get_col_names("user_addresses")
    if "user_addresses" in insp.get_table_names():
        if "formatted_address" not in addr_cols:
            op.add_column("user_addresses", sa.Column("formatted_address", sa.String(500), nullable=True))
        if "latitude" not in addr_cols:
            op.add_column("user_addresses", sa.Column("latitude", sa.Float(), nullable=True))
        if "longitude" not in addr_cols:
            op.add_column("user_addresses", sa.Column("longitude", sa.Float(), nullable=True))
        if "place_id" not in addr_cols:
            op.add_column("user_addresses", sa.Column("place_id", sa.String(100), nullable=True))
        if "source_provider" not in addr_cols:
            op.add_column("user_addresses", sa.Column("source_provider", sa.String(50), nullable=True))
        if "confidence" not in addr_cols:
            op.add_column("user_addresses", sa.Column("confidence", sa.Float(), nullable=True))

    # 2. orders
    order_cols = get_col_names("orders")
    if "orders" in insp.get_table_names():
        if "shipping_formatted_address" not in order_cols:
            op.add_column("orders", sa.Column("shipping_formatted_address", sa.String(500), nullable=True))
        if "shipping_latitude" not in order_cols:
            op.add_column("orders", sa.Column("shipping_latitude", sa.Float(), nullable=True))
        if "shipping_longitude" not in order_cols:
            op.add_column("orders", sa.Column("shipping_longitude", sa.Float(), nullable=True))


def downgrade() -> None:
    bind = op.get_bind()
    insp = inspect(bind)

    def get_col_names(table_name: str):
        if table_name in insp.get_table_names():
            return [c["name"] for c in insp.get_columns(table_name)]
        return []

    # 1. orders
    order_cols = get_col_names("orders")
    if "orders" in insp.get_table_names():
        if "shipping_longitude" in order_cols:
            op.drop_column("orders", "shipping_longitude")
        if "shipping_latitude" in order_cols:
            op.drop_column("orders", "shipping_latitude")
        if "shipping_formatted_address" in order_cols:
            op.drop_column("orders", "shipping_formatted_address")

    # 2. user_addresses
    addr_cols = get_col_names("user_addresses")
    if "user_addresses" in insp.get_table_names():
        if "confidence" in addr_cols:
            op.drop_column("user_addresses", "confidence")
        if "source_provider" in addr_cols:
            op.drop_column("user_addresses", "source_provider")
        if "place_id" in addr_cols:
            op.drop_column("user_addresses", "place_id")
        if "longitude" in addr_cols:
            op.drop_column("user_addresses", "longitude")
        if "latitude" in addr_cols:
            op.drop_column("user_addresses", "latitude")
        if "formatted_address" in addr_cols:
            op.drop_column("user_addresses", "formatted_address")
