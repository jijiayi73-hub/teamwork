"""
Chat Database Constraints and Migration Tests

This test suite verifies:
1. SQLite foreign_keys are automatically enabled via event listener
2. All CHECK constraints work correctly
3. All UNIQUE constraints work correctly
4. Foreign key CASCADE and RESTRICT behaviors work correctly
5. Source snapshot fields preserve data after diary deletion
6. Migration upgrade/downgrade cycle works correctly
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
import sqlalchemy
from sqlalchemy import create_engine, event, text

from app.config import settings
from app.database import Base, get_db
from app.models.chat import (
    Conversation,
    ConversationMode,
    Message,
    MessageRole,
    MessageSource,
    SourceType,
)
from app.models.diary import Diary, EmotionAnalysis, Entry, User


class TestForeignKeyEventListener:
    """Test that the SQLite foreign_keys event listener is configured correctly."""

    def test_foreign_keys_enabled_on_engine(self):
        """Verify that PRAGMA foreign_keys is ON when using the app's engine."""
        # Import the engine from database module
        from app.database import engine

        with engine.connect() as conn:
            result = conn.execute(text("PRAGMA foreign_keys")).scalar()
            assert result == 1, "foreign_keys should be ON"


class TestConversationConstraints:
    """Test conversation table constraints."""

    def test_companion_mode_rejects_anchor_diary(self, db_session):
        """companion mode must NOT have an anchor_diary_id."""
        # Create test user and diary
        user = User(email="test@example.com", username="test", password_hash="hash")
        db_session.add(user)
        db_session.flush()

        diary = create_test_diary(db_session, user.id)

        # Try to create companion conversation with anchor
        conversation = Conversation(
            user_id=user.id,
            mode=ConversationMode.COMPANION,
            title="Test",
            anchor_diary_id=diary.id,  # This should violate CHECK constraint
        )

        with pytest.raises(sqlalchemy.exc.IntegrityError):
            db_session.add(conversation)
            db_session.commit()

        db_session.rollback()

    def test_past_self_mode_requires_anchor_diary(self, db_session):
        """past_self mode MUST have an anchor_diary_id."""
        # Create test user
        user = User(email="test2@example.com", username="test2", password_hash="hash")
        db_session.add(user)
        db_session.flush()

        # Try to create past_self conversation without anchor
        conversation = Conversation(
            user_id=user.id,
            mode=ConversationMode.PAST_SELF,
            title="Test",
            anchor_diary_id=None,  # This should violate CHECK constraint
        )

        with pytest.raises(sqlalchemy.exc.IntegrityError):
            db_session.add(conversation)
            db_session.commit()

        db_session.rollback()

    def test_invalid_mode_rejected(self, db_session):
        """Invalid mode values are rejected by CHECK constraint."""
        user = User(email="test3@example.com", username="test3", password_hash="hash")
        db_session.add(user)
        db_session.flush()

        # Try to insert invalid mode directly
        with pytest.raises(sqlalchemy.exc.IntegrityError):
            db_session.execute(
                text(
                    """
                    INSERT INTO conversations (user_id, mode, title, created_at, updated_at)
                    VALUES (:uid, 'invalid_mode', 'Test', datetime('now'), datetime('now'))
                """
                ),
                {"uid": user.id},
            )
            db_session.commit()

        db_session.rollback()


class TestMessageSourceConstraints:
    """Test message_sources table constraints."""

    def test_relevance_score_bounds(self, db_session):
        """relevance_score must be between 0.0 and 1.0."""
        user = User(email="test4@example.com", username="test4", password_hash="hash")
        db_session.add(user)
        db_session.flush()

        conversation = Conversation(
            user_id=user.id, mode=ConversationMode.COMPANION, title="Test"
        )
        db_session.add(conversation)
        db_session.flush()

        message = Message(
            conversation_id=conversation.id,
            role=MessageRole.ASSISTANT,
            content="Test response",
        )
        db_session.add(message)
        db_session.flush()

        # Try relevance_score > 1.0
        with pytest.raises(sqlalchemy.exc.IntegrityError):
            source = MessageSource(
                message_id=message.id,
                source_type=SourceType.RETRIEVED,
                title_snapshot="Test",
                excerpt_snapshot="Test",
                relevance_score=1.5,  # Invalid
                rank=1,
            )
            db_session.add(source)
            db_session.commit()

        db_session.rollback()

    def test_rank_minimum_value(self, db_session):
        """rank must be >= 1."""
        user = User(email="test5@example.com", username="test5", password_hash="hash")
        db_session.add(user)
        db_session.flush()

        conversation = Conversation(
            user_id=user.id, mode=ConversationMode.COMPANION, title="Test"
        )
        db_session.add(conversation)
        db_session.flush()

        message = Message(
            conversation_id=conversation.id,
            role=MessageRole.ASSISTANT,
            content="Test response",
        )
        db_session.add(message)
        db_session.flush()

        # Try rank = 0
        with pytest.raises(sqlalchemy.exc.IntegrityError):
            source = MessageSource(
                message_id=message.id,
                source_type=SourceType.RETRIEVED,
                title_snapshot="Test",
                excerpt_snapshot="Test",
                relevance_score=0.8,
                rank=0,  # Invalid
            )
            db_session.add(source)
            db_session.commit()

        db_session.rollback()

    def test_duplicate_message_diary_rejected(self, db_session):
        """UNIQUE(message_id, diary_id) prevents duplicate sources."""
        user = User(email="test6@example.com", username="test6", password_hash="hash")
        db_session.add(user)
        db_session.flush()

        diary = create_test_diary(db_session, user.id)

        conversation = Conversation(
            user_id=user.id, mode=ConversationMode.COMPANION, title="Test"
        )
        db_session.add(conversation)
        db_session.flush()

        message = Message(
            conversation_id=conversation.id,
            role=MessageRole.ASSISTANT,
            content="Test response",
        )
        db_session.add(message)
        db_session.flush()

        # Create first source
        source1 = MessageSource(
            message_id=message.id,
            diary_id=diary.id,
            source_type=SourceType.RETRIEVED,
            title_snapshot="Test",
            excerpt_snapshot="Test",
            relevance_score=0.9,
            rank=1,
        )
        db_session.add(source1)
        db_session.commit()

        # Try to create duplicate
        with pytest.raises(sqlalchemy.exc.IntegrityError):
            source2 = MessageSource(
                message_id=message.id,
                diary_id=diary.id,  # Same diary
                source_type=SourceType.RETRIEVED,
                title_snapshot="Test2",
                excerpt_snapshot="Test2",
                relevance_score=0.8,
                rank=2,
            )
            db_session.add(source2)
            db_session.commit()

        db_session.rollback()

    def test_duplicate_rank_rejected(self, db_session):
        """UNIQUE(message_id, rank) prevents duplicate ranks."""
        user = User(email="test7@example.com", username="test7", password_hash="hash")
        db_session.add(user)
        db_session.flush()

        diary1 = create_test_diary(db_session, user.id, "Test1", "2024-01-01")
        diary2 = create_test_diary(db_session, user.id, "Test2", "2024-01-02")
        db_session.flush()

        conversation = Conversation(
            user_id=user.id, mode=ConversationMode.COMPANION, title="Test"
        )
        db_session.add(conversation)
        db_session.flush()

        message = Message(
            conversation_id=conversation.id,
            role=MessageRole.ASSISTANT,
            content="Test response",
        )
        db_session.add(message)
        db_session.flush()

        # Create first source with rank 1
        source1 = MessageSource(
            message_id=message.id,
            diary_id=diary1.id,
            source_type=SourceType.RETRIEVED,
            title_snapshot="Test1",
            excerpt_snapshot="Test1",
            relevance_score=0.9,
            rank=1,
        )
        db_session.add(source1)
        db_session.commit()

        # Try to create another source with same rank
        with pytest.raises(sqlalchemy.exc.IntegrityError):
            source2 = MessageSource(
                message_id=message.id,
                diary_id=diary2.id,
                source_type=SourceType.RETRIEVED,
                title_snapshot="Test2",
                excerpt_snapshot="Test2",
                relevance_score=0.8,
                rank=1,  # Duplicate rank
            )
            db_session.add(source2)
            db_session.commit()

        db_session.rollback()


class TestCascadeBehaviors:
    """Test foreign key CASCADE behaviors."""

    def test_delete_conversation_cascades_to_messages(self, db_session):
        """Deleting a conversation should CASCADE to messages."""
        user = User(email="test8@example.com", username="test8", password_hash="hash")
        db_session.add(user)
        db_session.flush()

        conversation = Conversation(
            user_id=user.id, mode=ConversationMode.COMPANION, title="Test"
        )
        db_session.add(conversation)
        db_session.flush()

        message = Message(
            conversation_id=conversation.id,
            role=MessageRole.USER,
            content="Test message",
        )
        db_session.add(message)
        db_session.commit()

        message_id = message.id
        conversation_id = conversation.id

        # Delete conversation
        db_session.delete(conversation)
        db_session.commit()

        # Verify message is deleted
        result = db_session.execute(
            text("SELECT id FROM messages WHERE id = :mid"), {"mid": message_id}
        ).first()
        assert result is None

    def test_delete_message_cascades_to_sources(self, db_session):
        """Deleting a message should CASCADE to message_sources."""
        user = User(email="test9@example.com", username="test9", password_hash="hash")
        db_session.add(user)
        db_session.flush()

        diary = create_test_diary(db_session, user.id)

        conversation = Conversation(
            user_id=user.id, mode=ConversationMode.COMPANION, title="Test"
        )
        db_session.add(conversation)
        db_session.flush()

        message = Message(
            conversation_id=conversation.id,
            role=MessageRole.ASSISTANT,
            content="Test response",
        )
        db_session.add(message)
        db_session.flush()

        source = MessageSource(
            message_id=message.id,
            diary_id=diary.id,
            source_type=SourceType.RETRIEVED,
            title_snapshot="Test",
            excerpt_snapshot="Test",
            relevance_score=0.9,
            rank=1,
        )
        db_session.add(source)
        db_session.commit()

        source_id = source.id

        # Delete message
        db_session.delete(message)
        db_session.commit()

        # Verify source is deleted
        result = db_session.execute(
            text("SELECT id FROM message_sources WHERE id = :sid"), {"sid": source_id}
        ).first()
        assert result is None


class TestRestrictBehavior:
    """Test foreign key RESTRICT behavior on anchor_diary_id."""

    def test_delete_anchor_diary_restricted(self, db_session):
        """Deleting a diary used as anchor should be RESTRICTed."""
        user = User(email="test10@example.com", username="test10", password_hash="hash")
        db_session.add(user)
        db_session.flush()

        diary = create_test_diary(db_session, user.id)

        conversation = Conversation(
            user_id=user.id,
            mode=ConversationMode.PAST_SELF,
            title="Test",
            anchor_diary_id=diary.id,  # Anchored to this diary
        )
        db_session.add(conversation)
        db_session.commit()

        # Try to delete the diary - should be RESTRICTed
        with pytest.raises(sqlalchemy.exc.IntegrityError):
            db_session.delete(diary)
            db_session.commit()

        db_session.rollback()


class TestSetNullBehavior:
    """Test foreign key SET NULL behavior on source diary_id."""

    def test_delete_source_diary_sets_null(self, db_session):
        """Deleting a diary used as source should SET diary_id to NULL."""
        user = User(email="test11@example.com", username="test11", password_hash="hash")
        db_session.add(user)
        db_session.flush()

        diary = create_test_diary(db_session, user.id, "Test diary content")

        conversation = Conversation(
            user_id=user.id, mode=ConversationMode.COMPANION, title="Test"
        )
        db_session.add(conversation)
        db_session.flush()

        message = Message(
            conversation_id=conversation.id,
            role=MessageRole.ASSISTANT,
            content="Test response",
        )
        db_session.add(message)
        db_session.flush()

        from datetime import date

        source = MessageSource(
            message_id=message.id,
            diary_id=diary.id,
            source_type=SourceType.RETRIEVED,
            diary_date_snapshot=date.fromisoformat("2024-01-01"),
            title_snapshot="Test Title",
            excerpt_snapshot="Test excerpt for snapshot",
            emotion_label_snapshot="happy",
            relevance_score=0.9,
            rank=1,
        )
        db_session.add(source)
        db_session.commit()

        source_id = source.id

        # Delete the diary
        db_session.delete(diary)
        db_session.commit()

        # Verify diary_id is now NULL but snapshots preserved
        result = db_session.execute(
            text(
                """
                SELECT diary_id, title_snapshot, excerpt_snapshot
                FROM message_sources
                WHERE id = :sid
            """
            ),
            {"sid": source_id},
        ).first()

        assert result is not None
        assert result[0] is None  # diary_id should be NULL
        assert result[1] == "Test Title"  # snapshot preserved
        assert result[2] == "Test excerpt for snapshot"  # snapshot preserved


class TestMigrationCycle:
    """Test Alembic migration upgrade/downgrade cycle."""

    @pytest.fixture
    def temp_db_path(self):
        """Create a temporary database file for migration testing."""
        fd, path = tempfile.mkstemp(suffix=".db", prefix="test_migration_")
        os.close(fd)
        yield path
        # Cleanup - Windows may have file locked, so use try/except
        try:
            if os.path.exists(path):
                os.remove(path)
        except PermissionError:
            pass  # Leave temp file for manual cleanup

    def test_migration_upgrade_downgrade_cycle(self, temp_db_path):
        """Test full migration cycle: upgrade → verify → downgrade → upgrade."""
        from alembic.config import Config
        from unittest.mock import patch
        import os

        # Create Alembic config for temporary database
        alembic_dir = Path(__file__).parent.parent / "alembic"
        config = Config()
        config.set_main_option("script_location", str(alembic_dir))
        config.set_main_option("sqlalchemy.url", f"sqlite:///{temp_db_path}")

        # Set environment variable to override settings
        test_url = f"sqlite:///{temp_db_path}"
        original_env = os.environ.get("DATABASE_URL")

        try:
            os.environ["DATABASE_URL"] = test_url

            # Force reload of settings to pick up new DATABASE_URL
            import importlib
            import app.config
            importlib.reload(app.config)
            from app.config import settings

            from alembic import command

            # 1. Upgrade to head
            command.upgrade(config, "head")

        finally:
            # Restore original environment
            if original_env:
                os.environ["DATABASE_URL"] = original_env
            else:
                os.environ.pop("DATABASE_URL", None)
            # Reload settings again
            import importlib
            import app.config
            importlib.reload(app.config)

        # 2. Verify current version is 0002 using direct SQL
        import sqlite3

        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT version_num FROM alembic_version")
        result = cursor.fetchone()
        conn.close()

        assert result is not None, "alembic_version table should exist"
        current_rev = result[0]
        assert current_rev == "0002", f"Expected revision 0002, got {current_rev}"

        # 3. Verify all tables exist
        from sqlalchemy import inspect

        engine = create_engine(f"sqlite:///{temp_db_path}")
        inspector = inspect(engine)
        tables = [t for t in inspector.get_table_names() if t != "alembic_version"]
        expected_tables = {
            "users",
            "entries",
            "emotion_analyses",
            "diaries",
            "conversations",
            "messages",
            "message_sources",
        }
        assert set(tables) == expected_tables, f"Expected {expected_tables}, got {set(tables)}"

        # 4. Downgrade to base
        original_env = os.environ.get("DATABASE_URL")
        try:
            os.environ["DATABASE_URL"] = test_url
            import importlib
            import app.config
            importlib.reload(app.config)
            command.downgrade(config, "base")
        finally:
            if original_env:
                os.environ["DATABASE_URL"] = original_env
            else:
                os.environ.pop("DATABASE_URL", None)
            import importlib
            import app.config
            importlib.reload(app.config)

        # 5. Verify all tables are dropped (alembic_version may remain)
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        # alembic_version table might still exist after downgrade
        expected_empty = set(tables) - {"alembic_version"}
        assert len(expected_empty) == 0, f"Expected no tables after downgrade, got {expected_empty}"

        # 6. Upgrade again to head
        original_env = os.environ.get("DATABASE_URL")
        try:
            os.environ["DATABASE_URL"] = test_url
            import importlib
            import app.config
            importlib.reload(app.config)
            command.upgrade(config, "head")
        finally:
            if original_env:
                os.environ["DATABASE_URL"] = original_env
            else:
                os.environ.pop("DATABASE_URL", None)
            import importlib
            import app.config
            importlib.reload(app.config)

        # 7. Verify current version is still 0002
        conn = sqlite3.connect(temp_db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT version_num FROM alembic_version")
        result = cursor.fetchone()
        conn.close()

        assert result is not None, "alembic_version table should exist after re-upgrade"
        current_rev = result[0]
        assert current_rev == "0002", f"Expected revision 0002 after re-upgrade, got {current_rev}"

        # 8. Verify tables are recreated
        inspector = inspect(engine)
        tables = [t for t in inspector.get_table_names() if t != "alembic_version"]
        assert set(tables) == expected_tables, f"Expected {expected_tables} after re-upgrade, got {set(tables)}"


# Test database isolation
@pytest.fixture(scope="function")
def test_db():
    """Create a test database that's isolated for each test."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    # Create an in-memory SQLite database for testing
    test_engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
    )

    # Enable foreign_keys
    from app.database import set_sqlite_foreign_keys

    # Import the event listener function and apply it
    from sqlalchemy import event

    @event.listens_for(test_engine, "connect")
    def _set_sqlite_foreign_keys(dbapi_conn, connection_record):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

    # Create all tables
    Base.metadata.create_all(bind=test_engine)

    # Create a session
    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    session = TestSessionLocal()

    yield session

    # Cleanup
    session.close()
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db_session(test_db):
    """Alias for test_db to maintain compatibility."""
    return test_db


def create_test_diary(db_session, user_id, content="Test diary", diary_date="2024-01-01"):
    """Helper to create a complete Diary with Entry and EmotionAnalysis."""
    from datetime import date

    entry = Entry(
        user_id=user_id,
        raw_content=content,
        status="completed",
    )
    db_session.add(entry)
    db_session.flush()

    analysis = EmotionAnalysis(
        entry_id=entry.id,
        primary_emotion="happy",
        emotion_score=5,
        valence=0.5,
        arousal=0.5,
        intensity=0.5,
        summary="Test summary",
        suggestion="Test suggestion",
    )
    db_session.add(analysis)
    db_session.flush()

    diary = Diary(
        user_id=user_id,
        entry_id=entry.id,
        analysis_id=analysis.id,
        title=content[:20],
        content=content,
        diary_date=date.fromisoformat(diary_date),
    )
    db_session.add(diary)
    db_session.flush()

    return diary
