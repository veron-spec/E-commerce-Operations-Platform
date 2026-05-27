"""Add user_id to stores (for databases created before user isolation)

Revision ID: 002
Revises: 001
Create Date: 2026-05-23
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add user_id column to stores (if running against old schema without it)
    op.add_column("stores", sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=True, index=True))


def downgrade() -> None:
    op.drop_column("stores", "user_id")
