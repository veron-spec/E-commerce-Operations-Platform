"""Add Taobao OAuth token fields to stores

Revision ID: 003
Revises: 002
Create Date: 2026-05-28
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("stores", sa.Column("session_key", sa.Text(), nullable=True, comment="Encrypted Taobao session_key (access_token)"))
    op.add_column("stores", sa.Column("refresh_token", sa.Text(), nullable=True, comment="Encrypted Taobao refresh_token"))
    op.add_column("stores", sa.Column("token_expires_at", sa.DateTime(), nullable=True, comment="Taobao access_token expiry"))


def downgrade() -> None:
    op.drop_column("stores", "token_expires_at")
    op.drop_column("stores", "refresh_token")
    op.drop_column("stores", "session_key")
