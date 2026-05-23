"""Initial schema

Revision ID: 001
Revises:
Create Date: 2026-05-19
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Stores
    op.create_table(
        "stores",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("platform_type", sa.String(50), nullable=False, comment="shopify, woocommerce, etc."),
        sa.Column("api_key", sa.Text(), nullable=False),
        sa.Column("api_secret", sa.Text(), nullable=False),
        sa.Column("store_url", sa.String(500), nullable=False),
        sa.Column("sync_config", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), default=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )

    # Products
    op.create_table(
        "products",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("store_id", sa.Integer(), sa.ForeignKey("stores.id"), nullable=False, index=True),
        sa.Column("platform_id", sa.String(255), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("price", sa.Float(), default=0),
        sa.Column("compare_at_price", sa.Float(), nullable=True),
        sa.Column("sku", sa.String(100), nullable=True, index=True),
        sa.Column("barcode", sa.String(100), nullable=True),
        sa.Column("category", sa.String(255), nullable=True),
        sa.Column("tags", JSONB(), nullable=True),
        sa.Column("images", JSONB(), nullable=True),
        sa.Column("status", sa.String(50), default="active"),
        sa.Column("inventory_quantity", sa.Integer(), default=0),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )

    # Orders
    op.create_table(
        "orders",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("store_id", sa.Integer(), sa.ForeignKey("stores.id"), nullable=False, index=True),
        sa.Column("platform_id", sa.String(255), nullable=False),
        sa.Column("order_number", sa.String(100), nullable=False, index=True),
        sa.Column("customer_platform_id", sa.String(255), nullable=True),
        sa.Column("email", sa.String(255), nullable=True),
        sa.Column("line_items", JSONB(), nullable=True),
        sa.Column("total_price", sa.Float(), default=0),
        sa.Column("subtotal_price", sa.Float(), default=0),
        sa.Column("total_discount", sa.Float(), default=0),
        sa.Column("shipping_info", JSONB(), nullable=True),
        sa.Column("financial_status", sa.String(50), nullable=True),
        sa.Column("fulfillment_status", sa.String(50), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), index=True),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )

    # Customers
    op.create_table(
        "customers",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("store_id", sa.Integer(), sa.ForeignKey("stores.id"), nullable=False, index=True),
        sa.Column("platform_id", sa.String(255), nullable=False),
        sa.Column("email", sa.String(255), nullable=True, index=True),
        sa.Column("first_name", sa.String(100), nullable=True),
        sa.Column("last_name", sa.String(100), nullable=True),
        sa.Column("orders_count", sa.Integer(), default=0),
        sa.Column("total_spent", sa.Float(), default=0),
        sa.Column("is_verified_email", sa.Boolean(), default=False),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )

    # Sync Jobs
    op.create_table(
        "sync_jobs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("store_id", sa.Integer(), sa.ForeignKey("stores.id"), nullable=False, index=True),
        sa.Column("sync_type", sa.String(50), nullable=False),
        sa.Column("status", sa.String(50), default="pending"),
        sa.Column("records_processed", sa.Integer(), default=0),
        sa.Column("records_failed", sa.Integer(), default=0),
        sa.Column("error_log", JSONB(), nullable=True),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )

    # Automation Rules
    op.create_table(
        "automation_rules",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("store_id", sa.Integer(), sa.ForeignKey("stores.id"), nullable=False, index=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("trigger_type", sa.String(50), nullable=False),
        sa.Column("conditions", JSONB(), nullable=True),
        sa.Column("actions", JSONB(), nullable=True),
        sa.Column("is_enabled", sa.Boolean(), default=True),
        sa.Column("last_run_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )

    # Report Cache
    op.create_table(
        "report_cache",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("store_id", sa.Integer(), sa.ForeignKey("stores.id"), nullable=False, index=True),
        sa.Column("report_type", sa.String(100), nullable=False),
        sa.Column("period_start", sa.DateTime(), nullable=False),
        sa.Column("period_end", sa.DateTime(), nullable=False),
        sa.Column("data", JSONB(), nullable=True),
        sa.Column("generated_at", sa.DateTime(), server_default=sa.func.now()),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("report_cache")
    op.drop_table("automation_rules")
    op.drop_table("sync_jobs")
    op.drop_table("customers")
    op.drop_table("orders")
    op.drop_table("products")
    op.drop_table("stores")
