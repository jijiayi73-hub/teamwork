"""fix_message_sources_schema

Revision ID: b76715ea8730
Revises: 0003
Create Date: 2026-07-08 23:30:42.275854

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b76715ea8730'
down_revision: Union[str, Sequence[str], None] = '0003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - add missing snapshot columns to message_sources.

    The message_sources table was created with old schema missing:
    - diary_date_snapshot
    - title_snapshot
    - emotion_label_snapshot
    And 'excerpt' should be 'excerpt_snapshot'.

    Since SQLite has limited ALTER TABLE support, we recreate the table.
    """
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    table_names = inspector.get_table_names()

    if 'message_sources_new' in table_names:
        op.drop_table('message_sources_new')

    if 'message_sources' not in table_names:
        return

    existing_columns = {column['name'] for column in inspector.get_columns('message_sources')}
    if 'excerpt_snapshot' in existing_columns and 'excerpt' not in existing_columns:
        return

    if 'excerpt' not in existing_columns:
        raise RuntimeError("message_sources table is missing both excerpt and excerpt_snapshot columns")

    # Get existing data
    op.execute("""
        CREATE TABLE message_sources_new (
            id INTEGER PRIMARY KEY,
            message_id INTEGER NOT NULL,
            diary_id INTEGER,
            source_type VARCHAR(20) NOT NULL,
            diary_date_snapshot DATE,
            title_snapshot VARCHAR(120) NOT NULL,
            excerpt_snapshot TEXT NOT NULL,
            emotion_label_snapshot VARCHAR(30),
            relevance_score FLOAT NOT NULL,
            rank INTEGER NOT NULL,
            created_at DATETIME NOT NULL,
            FOREIGN KEY(diary_id) REFERENCES diaries(id) ON DELETE SET NULL,
            FOREIGN KEY(message_id) REFERENCES messages(id) ON DELETE CASCADE,
            CHECK(source_type IN ('anchor', 'retrieved')),
            CHECK(rank >= 1),
            CHECK(relevance_score >= 0.0 AND relevance_score <= 1.0),
            UNIQUE(message_id, diary_id),
            UNIQUE(message_id, rank)
        )
    """)

    # Copy existing data, mapping excerpt to excerpt_snapshot
    # For missing snapshot fields, use default values
    op.execute("""
        INSERT INTO message_sources_new
            (id, message_id, diary_id, source_type, diary_date_snapshot, title_snapshot,
             excerpt_snapshot, emotion_label_snapshot, relevance_score, rank, created_at)
        SELECT
            id, message_id, diary_id, source_type, NULL, 'Untitled',
             excerpt, NULL, relevance_score, rank, created_at
        FROM message_sources
    """)

    # Drop old table and rename new one
    op.drop_table('message_sources')
    op.execute("ALTER TABLE message_sources_new RENAME TO message_sources")

    # Recreate indexes
    op.create_index('ix_message_sources_diary_id', 'message_sources', ['diary_id'])
    op.create_index('ix_message_sources_id', 'message_sources', ['id'])
    op.create_index('ix_message_sources_message_id', 'message_sources', ['message_id'])


def downgrade() -> None:
    """Downgrade schema - revert to old message_sources structure."""
    # Create old-style table
    op.execute("""
        CREATE TABLE message_sources_old (
            id INTEGER PRIMARY KEY,
            message_id INTEGER NOT NULL,
            diary_id INTEGER,
            source_type VARCHAR(20) NOT NULL,
            excerpt TEXT NOT NULL,
            relevance_score FLOAT NOT NULL,
            rank INTEGER NOT NULL,
            created_at DATETIME NOT NULL,
            FOREIGN KEY(diary_id) REFERENCES diaries(id) ON DELETE SET NULL,
            FOREIGN KEY(message_id) REFERENCES messages(id) ON DELETE CASCADE
        )
    """)

    # Copy data, mapping excerpt_snapshot back to excerpt
    op.execute("""
        INSERT INTO message_sources_old
            (id, message_id, diary_id, source_type, excerpt, relevance_score, rank, created_at)
        SELECT
            id, message_id, diary_id, source_type, excerpt_snapshot, relevance_score, rank, created_at
        FROM message_sources
    """)

    # Drop current table and rename old one
    op.drop_table('message_sources')
    op.execute("ALTER TABLE message_sources_old RENAME TO message_sources")

    # Recreate indexes
    op.create_index('ix_message_sources_diary_id', 'message_sources', ['diary_id'])
    op.create_index('ix_message_sources_id', 'message_sources', ['id'])
    op.create_index('ix_message_sources_message_id', 'message_sources', ['message_id'])
