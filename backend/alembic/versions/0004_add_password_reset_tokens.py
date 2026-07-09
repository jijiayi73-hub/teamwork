"""Add password reset token fields to users table

Revision ID: 0004
Revises: b76715ea8730
Create Date: 2026-07-09 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0004"
down_revision: Union[str, Sequence[str], None] = "b76715ea8730"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add password reset token fields
    op.add_column("users", sa.Column("reset_token", sa.String(length=255), nullable=True))
    op.add_column("users", sa.Column("reset_token_expires_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index(op.f("ix_users_reset_token"), "users", ["reset_token"], unique=True)


def downgrade() -> None:
    op.drop_index(op.f("ix_users_reset_token"), table_name="users")
    op.drop_column("users", "reset_token_expires_at")
    op.drop_column("users", "reset_token")
