# Log 13 - Migration Hardening and Database Constraints

## Date and Branch

- Date: 2026-07-08
- Branch: `backend/chat-database-schema`

## User Request

对chat数据库迁移进行加固和修复，确保：
1. 迁移链正确且可重入
2. SQLite外键约束正确启用
3. 业务约束在数据库层面得到保障
4. 消息来源支持历史快照（日记删除后仍可显示）

## Source Docs Read

- `docs/vibe-logs/log-12-chat-database-schema.md`
- `backend/alembic/versions/5774908a021a_initial_database_schema_with_users_.py` (deleted)
- `backend/app/models/chat.py`
- `backend/app/database.py`
- `backend/alembic/env.py`

## Files Changed

### Modified Files

- `backend/app/database.py` - Added SQLite foreign_keys event listener
- `backend/app/models/chat.py` - Added snapshot fields and CHECK constraints
- `backend/alembic/env.py` - Added SQLite foreign_keys event listener
- `docs/vibe-logs/log-07-rag-chat-api-design.md` - Updated snapshot documentation
- `docs/vibe-logs/log-12-chat-database-schema.md` - Added audit log section

### New Files Created

- `backend/alembic/versions/0001_baseline_core_schema.py` - Baseline schema migration
- `backend/alembic/versions/0002_add_chat_schema.py` - Chat schema migration

### Deleted Files

- `backend/alembic/versions/5774908a021a_initial_database_schema_with_users_.py` - Replaced by split migrations

## Key Decisions and Architecture Constraints

### 1. Migration Split Strategy

**Problem**: Original single migration `5774908a021a` claimed to create all tables but only created chat tables.

**Solution**: Split into two migrations:

| Migration | Revision | Creates | Dependencies |
|-----------|----------|---------|--------------|
| Baseline Core | `0001` | users, entries, emotion_analyses, diaries | None (base) |
| Add Chat Schema | `0002` | conversations, messages, message_sources | 0001 |

**Benefits**:
- Clean separation of concerns
- Each migration has a single, clear purpose
- Easier to debug and rollback
- Supports future schema evolution

### 2. SQLite Foreign Keys Enablement

**Problem**: SQLite does not enable foreign keys by default, causing cascade behaviors to fail silently.

**Solution**: Added event listeners in two locations:

```python
# backend/app/database.py
@event.listens_for(Engine, "connect")
def set_sqlite_foreign_keys(dbapi_conn, connection_record):
    if "sqlite" in str(dbapi_conn.__class__):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
```

```python
# backend/alembic/env.py
@event.listens_for(Engine, "connect")
def set_sqlite_foreign_keys(dbapi_conn, connection_record):
    if "sqlite" in str(dbapi_conn.__class__):
        cursor = dbapi_conn.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()
```

**Why both locations**:
- `database.py`: Ensures runtime foreign keys for application
- `env.py`: Ensures foreign keys during migration execution

### 3. Conversation Mode-Anchor Constraint

**Problem**: No database constraint ensuring mode and anchor_diary_id consistency.

**Business Rules**:
- `companion` mode: 必须 没有 anchor_diary_id
- `past_self` mode: 必须 有 anchor_diary_id

**Solution**: Added CHECK constraint:

```sql
CHECK (
    (mode = 'companion' AND anchor_diary_id IS NULL) OR
    (mode = 'past_self' AND anchor_diary_id IS NOT NULL)
)
```

**Benefits**:
- Database-level validation prevents invalid states
- Reduces service layer validation burden
- Clear error messages on constraint violation

### 4. Anchor Diary FK Strategy

**Problem**: Original `anchor_diary_id` used `SET NULL`, but past_self conversations require valid anchor.

**Solution**: Changed to `ON DELETE RESTRICT`:

```python
anchor_diary_id: Mapped[Optional[int]] = mapped_column(
    ForeignKey("diaries.id", ondelete="RESTRICT"),  # Changed from SET NULL
    nullable=True,
    index=True
)
```

**Rationale**:
- past_self conversations are semantically tied to a specific diary
- Deleting that diary should break the conversation (not silently nullify)
- Forces explicit handling of anchored conversation lifecycle

### 5. MessageSource Snapshot Fields

**Problem**: Original `excerpt` field insufficient for historical source display after diary deletion.

**Solution**: Added comprehensive snapshot fields:

| Field | Type | Purpose |
|-------|------|---------|
| `diary_date_snapshot` | DATE | Preserve diary date for display |
| `title_snapshot` | VARCHAR(120) | Preserve diary title |
| `excerpt_snapshot` | TEXT | Preserve relevant excerpt |
| `emotion_label_snapshot` | VARCHAR(30) | Preserve emotion context |

**Snapshot Semantics**:
- When diary is used as source, relevant fields are snapshotted
- After diary deletion, `diary_id` becomes NULL but snapshots remain
- Service layer must populate snapshot fields on source creation
- Historical sources remain displayable even after diary deletion

### 6. Unique Constraints on MessageSource

**Problem**: Missing constraint for rank uniqueness.

**Solution**: Added two unique constraints:

```sql
-- Prevent duplicate diary per message
UNIQUE(message_id, diary_id)

-- Ensure consistent ordering
UNIQUE(message_id, rank)
```

**Benefits**:
- Prevents duplicate sources
- Ensures deterministic ordering
- Clear error messages on constraint violation

## Implementation Steps

### 1. Split Migrations

Created two new migration files:

```bash
# 0001_baseline_core_schema.py
revision = '0001'
down_revision = None  # Base migration
```

```bash
# 0002_add_chat_schema.py
revision = '0002'
down_revision = '0001'
```

### 2. Add Foreign Keys Event Listeners

Added identical listeners to:
- `backend/app/database.py`
- `backend/alembic/env.py`

### 3. Update Model Constraints

Modified `backend/app/models/chat.py`:
- Added `ck_conversation_mode_anchor` CHECK constraint
- Changed `anchor_diary_id` FK to `RESTRICT`
- Added snapshot fields to `MessageSource`
- Added `uq_message_source_message_rank` unique constraint

### 4. Update Documentation

- Updated `log-07-rag-chat-api-design.md` with snapshot semantics
- Added audit log section to `log-12-chat-database-schema.md`

## Verification

### 1. Empty Database Migration

```bash
DATABASE_URL="sqlite:///test.db" py -m alembic upgrade head
```

**Result**: ✅ All 7 tables created successfully:
- users
- entries
- emotion_analyses
- diaries
- conversations
- messages
- message_sources

### 2. Migration Chain Verification

```bash
py -m alembic heads
# Output: 0002 (head)

py -m alembic history
# Output:
# <base> -> 0001, Baseline core schema
# 0001 -> 0002 (head), Add chat schema
```

**Result**: ✅ Single head, clean chain

### 3. Foreign Key Behaviors

Tested on temporary database:

| Scenario | Expected | Actual |
|----------|----------|--------|
| Delete conversation | Messages cascade deleted | ✅ |
| Delete anchored diary | RESTRICT blocks deletion | ✅ |
| Delete source diary | diary_id becomes NULL | ✅ |
| Snapshot preserved after deletion | Fields intact | ✅ |

### 4. CHECK Constraints

| Constraint | Test | Result |
|------------|------|--------|
| `ck_conversation_mode` | mode='invalid' | ✅ Blocked |
| `ck_conversation_mode_anchor` | companion + anchor_diary_id | ✅ Blocked |
| `ck_conversation_mode_anchor` | past_self + null anchor | ✅ Blocked |
| `ck_relevance_score` | score=1.5 | ✅ Blocked |
| `ck_rank` | rank=0 | ✅ Blocked |

### 5. UNIQUE Constraints

| Constraint | Test | Result |
|------------|------|--------|
| `uq_message_source_message_diary` | Duplicate (message_id, diary_id) | ✅ Blocked |
| `uq_message_source_message_rank` | Duplicate (message_id, rank) | ✅ Blocked |

### 6. Pytest Results

```bash
py -m pytest tests/ -q
# Output: 91 passed, 1 warning
```

**Result**: ✅ All tests passing, no regressions

## Risks and Blockers

### 1. Existing Development Database

**Problem**: Current development database has old revision `5774908a021a` which no longer exists.

**Impact**:
- `alembic current` fails with "Can't locate revision identified by '5774908a021a'"
- Cannot run migrations on existing database

**Mitigation**:
- Option 1: Delete and recreate database
- Option 2: Use `alembic stamp 0002` to mark current revision

### 2. Migration Re-entrancy

**Status**: ✅ Verified
- Empty database can upgrade to head
- Downgrade to base works
- Re-upgrade recreates all tables correctly

### 3. No Reports Feature

**Finding**: No `reports` table exists in codebase.

**Impact**:
- Documentation references to "reports" may be outdated
- No action needed unless feature is added later

## Next Requirement Plan

### 1. Migration Cleanup

**Action Items**:
- Recreate development database with new migrations
- Verify production migration strategy
- Document migration procedure for deployment

### 2. Service Layer Implementation

**Files**: `backend/app/services/chat_service.py`

**Requirements**:
- Populate snapshot fields when creating MessageSource
- Validate mode/anchor_diary_id consistency before database write
- Handle RESTRICT constraint when attempting to delete anchored diaries

### 3. API Layer Implementation

**Files**: `backend/app/routers/chat.py`, `backend/app/schemas/chat.py`

**Requirements**:
- Include snapshot fields in MessageSource schema
- Return snapshot data in chat history responses
- Handle constraint violations with appropriate error messages

### 4. Frontend Integration

**Files**: `frontend/src/types/chat.ts`, `frontend/src/api/chat.ts`

**Requirements**:
- Update TypeScript types to include snapshot fields
- Display source snapshots in chat UI
- Handle deleted diary references gracefully

## Database Schema Status: **HARDENED**

所有迁移问题已修复，数据库约束已加固。空数据库可以成功迁移到 head，所有外键和约束行为已验证。

---

## Audit Summary

### Issues Fixed

| Issue | Severity | Status |
|-------|----------|--------|
| Migration chain structure | High | ✅ Fixed |
| SQLite foreign keys disabled | High | ✅ Fixed |
| Mode-anchor consistency | Medium | ✅ Fixed |
| Anchor diary FK strategy | Medium | ✅ Fixed |
| Missing snapshot fields | Medium | ✅ Fixed |
| Missing unique constraints | Low | ✅ Fixed |

### Migration Chain (Final)

```
<base>
 └─ 0001_baseline_core_schema.py
     └─ 0002_add_chat_schema.py (head)
```

### Verification Checklist

- ✅ Empty database can upgrade to head
- ✅ Single head in alembic
- ✅ All foreign keys enabled
- ✅ All CHECK constraints working
- ✅ All UNIQUE constraints working
- ✅ Snapshot fields functional
- ✅ 91 tests passing
- ✅ No regressions introduced
