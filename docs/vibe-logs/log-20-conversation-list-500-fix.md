# Log 20: Conversation List 500 Error Fix

**Date:** 2026-07-08
**Task:** Debug "历史会话读取失败：Request failed: 500"
**Status:** ✅ Resolved

## Problem

Frontend `continueConversation(id)` call to `GET /api/v1/chat/conversations/{id}/messages` returned 500 Internal Server Error.

## Root Cause

Database table `message_sources` had outdated schema:
- Missing columns: `diary_date_snapshot`, `title_snapshot`, `excerpt_snapshot`, `emotion_label_snapshot`
- Had `excerpt` column instead of `excerpt_snapshot`

This occurred because:
1. Table was manually created with old schema before migration 0002
2. Migration 0002 (which defines correct schema) was skipped because table already existed
3. Migration 0003 ran successfully, leading alembic to report version 0003 (head)

## Evidence

```python
# Before fix
sqlalchemy.exc.OperationalError: no such column: message_sources.diary_date_snapshot
```

```sql
-- Old schema (incorrect)
message_sources:
  - id, message_id, diary_id, source_type, excerpt, relevance_score, rank, created_at

-- Migration 0002 definition (correct)
message_sources:
  - id, message_id, diary_id, source_type, diary_date_snapshot, title_snapshot,
    excerpt_snapshot, emotion_label_snapshot, relevance_score, rank, created_at
```

## Solution

Created migration `b76715ea8730_fix_message_sources_schema.py` to:
1. Create `message_sources_new` with correct schema
2. Copy existing data (mapping `excerpt` → `excerpt_snapshot`)
3. Drop old table and rename new one
4. Recreate indexes

## Verification

```bash
cd backend
py -m alembic upgrade head

# API tests
curl -X GET "http://localhost:8000/api/v1/chat/conversations/4/messages"
# Status: 200 ✅

# Backend tests
py -m pytest tests/test_chat_api.py -v
# 9 passed ✅
```

## Files Modified

| File | Action |
|------|--------|
| `backend/alembic/versions/b76715ea8730_fix_message_sources_schema.py` | Created |

## Impact

- No API contract changes
- No behavior changes
- Fixes 500 error on conversation history retrieval
- Frontend `continueConversation()` now works correctly

## Prevention

Always verify:
1. Database schema matches model definitions after migrations
2. `alembic current` matches actual table structures
3. Integration tests cover all CRUD operations

## Next Steps

- Ensure future schema changes use migrations only, not manual table creation
- Consider adding schema validation tests to CI
