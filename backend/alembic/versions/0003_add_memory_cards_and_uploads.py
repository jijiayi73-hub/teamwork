"""Add memory cards and uploaded assets

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-08 21:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0003"
down_revision: Union[str, Sequence[str], None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "memory_cards",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("diary_id", sa.Integer(), nullable=False),
        sa.Column("cover_image_url", sa.String(length=500), nullable=True),
        sa.Column("cover_prompt", sa.Text(), nullable=True),
        sa.Column("emotion_label", sa.String(length=30), nullable=False),
        sa.Column("emotion_color", sa.String(length=40), nullable=False),
        sa.Column("keywords_json", sa.Text(), nullable=False),
        sa.Column("conversation_summary", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["diary_id"], ["diaries.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("diary_id"),
    )
    op.create_index(op.f("ix_memory_cards_id"), "memory_cards", ["id"], unique=False)
    op.create_index(op.f("ix_memory_cards_user_id"), "memory_cards", ["user_id"], unique=False)
    op.create_index(op.f("ix_memory_cards_diary_id"), "memory_cards", ["diary_id"], unique=False)

    op.create_table(
        "uploaded_assets",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("stored_filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=100), nullable=False),
        sa.Column("url", sa.String(length=500), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("stored_filename"),
    )
    op.create_index(op.f("ix_uploaded_assets_id"), "uploaded_assets", ["id"], unique=False)
    op.create_index(op.f("ix_uploaded_assets_user_id"), "uploaded_assets", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_uploaded_assets_user_id"), table_name="uploaded_assets")
    op.drop_index(op.f("ix_uploaded_assets_id"), table_name="uploaded_assets")
    op.drop_table("uploaded_assets")
    op.drop_index(op.f("ix_memory_cards_diary_id"), table_name="memory_cards")
    op.drop_index(op.f("ix_memory_cards_user_id"), table_name="memory_cards")
    op.drop_index(op.f("ix_memory_cards_id"), table_name="memory_cards")
    op.drop_table("memory_cards")
