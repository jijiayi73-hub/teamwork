from __future__ import annotations

from datetime import date, timedelta

from app.models.diary import Diary, EmotionAnalysis, Entry, User
from app.services.retrieval_service import (
    AnchorContextualStrategy,
    AnchorTimeFollowupStrategy,
    KeywordEmotionTimeStrategy,
    NoRetrievalStrategy,
    get_strategy,
    retrieve_context,
)


def create_user(db_session, name: str = "retrieval") -> User:
    user = User(
        username=name,
        email=f"{name}@example.com",
        password_hash="hash",
        role="user",
        status="active",
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def create_diary(db_session, user_id: int, title: str, content: str, days: int) -> Diary:
    entry = Entry(user_id=user_id, raw_content=content, status="completed")
    db_session.add(entry)
    db_session.flush()
    analysis = EmotionAnalysis(
        entry_id=entry.id,
        primary_emotion="joy",
        emotion_score=5,
        valence=0.8,
        arousal=0.5,
        intensity=0.6,
        summary="summary",
        suggestion="suggestion",
    )
    db_session.add(analysis)
    db_session.flush()
    diary = Diary(
        user_id=user_id,
        entry_id=entry.id,
        analysis_id=analysis.id,
        title=title,
        content=content,
        diary_date=date.today() + timedelta(days=days),
    )
    db_session.add(diary)
    db_session.commit()
    db_session.refresh(diary)
    return diary


def test_no_retrieval_returns_empty(db_session):
    user = create_user(db_session)
    assert NoRetrievalStrategy(db_session, user.id).retrieve("anything") == []
    results, strategy = retrieve_context(db_session, user.id, "anything", use_memory=False)
    assert results == []
    assert strategy == "none"


def test_keyword_strategy_returns_only_current_user_matches(db_session):
    user = create_user(db_session, "kwuser")
    other = create_user(db_session, "kwother")
    own = create_diary(db_session, user.id, "Beach day", "happy beach memory", -1)
    create_diary(db_session, other.id, "Beach other", "happy beach memory", -1)

    results = KeywordEmotionTimeStrategy(db_session, user.id).retrieve("beach happy")

    assert [item.diary.id for item in results] == [own.id]
    assert results[0].source_type == "retrieved"


def test_anchor_contextual_and_followup_strategies(db_session):
    user = create_user(db_session, "anchoruser")
    anchor = create_diary(db_session, user.id, "Anchor", "anchor memory", 0)
    nearby = create_diary(db_session, user.id, "Nearby", "nearby memory", 3)
    later = create_diary(db_session, user.id, "Later", "later memory", 20)
    create_diary(db_session, user.id, "Too late", "late memory", 40)

    contextual = AnchorContextualStrategy(db_session, user.id).retrieve(
        "memory", anchor_diary_id=anchor.id
    )
    assert contextual[0].diary.id == anchor.id
    assert nearby.id in [item.diary.id for item in contextual]

    followup = AnchorTimeFollowupStrategy(db_session, user.id).retrieve(
        "memory", anchor_diary_id=anchor.id
    )
    assert followup[0].diary.id == anchor.id
    assert later.id in [item.diary.id for item in followup]
    assert all(item.diary.diary_date <= anchor.diary_date + timedelta(days=30) for item in followup)


def test_strategy_selection(db_session):
    user = create_user(db_session, "selector")
    anchor = create_diary(db_session, user.id, "Anchor", "anchor memory", 0)

    assert get_strategy("none") is NoRetrievalStrategy
    assert get_strategy("keyword_emotion_time") is KeywordEmotionTimeStrategy
    assert get_strategy("missing") is NoRetrievalStrategy

    _, strategy = retrieve_context(db_session, user.id, "memory", True, mode="companion")
    assert strategy == "keyword_emotion_time"
    _, strategy = retrieve_context(
        db_session,
        user.id,
        "memory",
        True,
        mode="past_self",
        anchor_diary_id=anchor.id,
        is_followup=False,
    )
    assert strategy == "anchor_contextual"
    _, strategy = retrieve_context(
        db_session,
        user.id,
        "memory",
        True,
        mode="past_self",
        anchor_diary_id=anchor.id,
        is_followup=True,
    )
    assert strategy == "anchor_time_followup"
