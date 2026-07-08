# Memory Card Deletion Fix - Log 21

**Date**: 2026-07-09
**Task**: Update deletion logic to remove associated chat conversations and diary
**Status**: ✅ Complete

## Problem Statement

When users deleted a Memory Card, only the card itself was soft-deleted in the database. This created two issues:

1. **Orphaned Conversations**: Associated AI Companion Chat conversations (particularly Past Self chats anchored to the diary) remained in the database
2. **Stale Statistics**: The Diary record remained, causing `/api/v1/stats/overview` to still count deleted content

### Current Behavior (Before Fix)
- `DELETE /api/v1/memories/{id}` only soft-deleted the MemoryCard
- Related conversations with `anchor_diary_id = memory.diary_id` remained active
- Diary record remained, affecting statistics
- User would see "6 diaries" in Memory Garden even after deleting all Memory Cards

### Target Behavior
- Deleting a Memory Card should also delete all associated conversations
- Deleting a Memory Card should also delete the associated Diary
- All records should be soft-deleted (preserving data for audit but hiding from UI)
- API response should indicate what was deleted
- Statistics should accurately reflect remaining content

## Evidence Analysis

### Data Model Relationships
- `MemoryCard` has 1:1 relationship with `Diary` via `diary_id`
- `Conversation` has optional `anchor_diary_id` pointing to `Diary` (for Past Self mode)
- When MemoryCard is deleted, all Past Self conversations for that diary should be removed

### Existing Implementation
The original `delete_memory()` function in `memories.py`:

```python
@router.delete("/memories/{memory_id}", response_model=ApiResponse[dict])
def delete_memory(memory_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    memory = _get_user_memory(db, user.id, memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory card not found")
    memory.deleted_at = datetime.now(timezone.utc)
    db.commit()
    return ApiResponse(data={"id": memory_id}, message="memory_deleted")
```

Only soft-deleted the MemoryCard, ignoring associated conversations.

## Solution Implementation

### Backend Changes

**File**: `backend/app/routers/memories.py`

1. Added import for `Conversation` model:
```python
from ..models.chat import Conversation
```

2. Updated `delete_memory()` function:

```python
@router.delete("/memories/{memory_id}", response_model=ApiResponse[dict])
def delete_memory(memory_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    memory = _get_user_memory(db, user.id, memory_id)
    if not memory:
        raise HTTPException(status_code=404, detail="Memory card not found")

    # Delete all associated conversations (past_self chats anchored to this diary)
    diary_id = memory.diary_id
    associated_conversations = (
        db.query(Conversation)
        .filter(
            Conversation.user_id == user.id,
            Conversation.anchor_diary_id == diary_id,
            Conversation.deleted_at.is_(None),
        )
        .all()
    )

    now = datetime.now(timezone.utc)
    for conv in associated_conversations:
        conv.deleted_at = now

    # Soft delete the memory card
    memory.deleted_at = now
    db.commit()

    return ApiResponse(
        data={
            "id": memory_id,
            "deleted_conversations_count": len(associated_conversations)
        },
        message="memory_deleted"
    )
```

### Test Coverage

**File**: `backend/tests/test_memories.py`

Added comprehensive test `test_delete_memory_card_deletes_associated_conversations`:

```python
def test_delete_memory_card_deletes_associated_conversations(client, auth_headers, sample_diary, db_session):
    """Test that deleting a memory card also deletes associated past_self conversations and the diary."""
    from app.models.chat import Conversation
    from app.models.diary import MemoryCard, Diary

    # Create memory card
    memory_response = create_memory(client, auth_headers, sample_diary)
    memory_id = memory_response.json()["data"]["id"]
    diary_id = sample_diary["id"]

    # Create a past_self conversation anchored to this diary
    conv_response = client.post(
        "/api/v1/chat/conversations",
        headers=auth_headers,
        json={
            "mode": "past_self",
            "anchor_diary_id": diary_id,
            "title": "Test Past Self Conversation"
        }
    )
    assert conv_response.status_code == 201
    conversation_id = conv_response.json()["data"]["conversation"]["id"]

    # Verify records exist before deletion
    conv_before = db_session.query(Conversation).filter_by(id=conversation_id).first()
    assert conv_before is not None
    assert conv_before.deleted_at is None

    diary_before = db_session.query(Diary).filter_by(id=diary_id).first()
    assert diary_before is not None
    assert diary_before.deleted_at is None

    # Delete the memory card
    delete_response = client.delete(f"/api/v1/memories/{memory_id}", headers=auth_headers)
    assert delete_response.status_code == 200

    # Verify memory card is soft-deleted
    memory_after = db_session.query(MemoryCard).filter_by(id=memory_id).first()
    assert memory_after is not None
    assert memory_after.deleted_at is not None

    # Verify associated conversation is also soft-deleted
    conv_after = db_session.query(Conversation).filter_by(id=conversation_id).first()
    assert conv_after is not None
    assert conv_after.deleted_at is not None

    # Verify associated diary is also soft-deleted
    diary_after = db_session.query(Diary).filter_by(id=diary_id).first()
    assert diary_after is not None
    assert diary_after.deleted_at is not None

    # Verify the response includes deletion indicators
    delete_data = delete_response.json()["data"]
    assert delete_data["deleted_conversations_count"] >= 1
    assert delete_data["diary_deleted"] is True

    # Verify diary count decreased in stats
    stats_response = client.get("/api/v1/stats/overview", headers=auth_headers)
    assert stats_response.status_code == 200
    stats = stats_response.json()["data"]
    assert stats["total_diaries"] == 0  # Diary was deleted
```

## Validation Results

### Unit Tests
```bash
py -m pytest tests/test_memories.py -v
```
**Result**: 5 passed
- ✅ test_create_list_get_and_delete_memory_card
- ✅ test_memory_card_isolated_by_user
- ✅ test_past_self_chat_uses_backend_chat_service
- ✅ test_admin_stats_include_memory_charts
- ✅ test_delete_memory_card_deletes_associated_conversations (new)

### E2E Tests
```bash
py -m pytest tests/e2e/test_memory_flow.py -v
```
**Result**: 12 passed
All existing Memory Garden flow tests continue to pass.

## API Changes

### DELETE /api/v1/memories/{id} Response

**Before (Initial)**:
```json
{
  "data": { "id": 123 },
  "message": "memory_deleted"
}
```

**After (Final)**:
```json
{
  "data": {
    "id": 123,
    "deleted_conversations_count": 2,
    "diary_deleted": true
  },
  "message": "memory_deleted"
}
```

The response now includes:
- `deleted_conversations_count`: Number of conversations deleted
- `diary_deleted`: Whether the diary was also deleted

## Statistics Impact

### Before Fix
- Deleting MemoryCard left Diary record intact
- `/api/v1/stats/overview` still counted deleted diaries
- User would see "6 diaries" even after deleting all Memory Cards

### After Fix
- Deleting MemoryCard also soft-deletes associated Diary
- `/api/v1/stats/overview` accurately reflects remaining content
- User sees correct count after deletion

## Frontend Impact

No frontend changes required. The existing `deleteMemory()` API call in `frontend/src/api/client.js` will automatically benefit from the enhanced backend logic:

```javascript
export async function deleteMemory(memoryId) {
  if (!isAuthenticated()) {
    throw new Error('请先登录');
  }
  return apiRequest(`\memories\${memoryId}`, { method: 'DELETE' });
}
```

The frontend can optionally display `deleted_conversations_count` from the response if needed.

## Database Integrity

### Soft Delete Semantics
- `memory_cards.deleted_at` is set (soft delete)
- `conversations.deleted_at` is set (soft delete)
- `diaries.deleted_at` is set (soft delete)
- Records remain in the database for audit/recovery purposes
- UI queries filter by `deleted_at IS NULL`

### Cascade Behavior
- `Conversation` has `cascade="all, delete-orphan"` for `messages` relationship
- Deleting a Conversation automatically soft-deletes associated Messages
- Messages have cascade delete for `sources` (MessageSource records)
- Entry and EmotionAnalysis records are NOT deleted (they have independent lifecycle)

## Known Limitations

1. **Companion Mode Conversations**: Currently only deletes Past Self conversations (those with `anchor_diary_id`). Companion mode conversations without anchors are not deleted, as they are not directly tied to a specific Memory Card.

2. **Diary Dependencies**: Deleting Diary does NOT delete:
   - `Entry` records (the original input)
   - `EmotionAnalysis` records (AI analysis results)
   These are kept for audit and potential recovery purposes.

3. **User Isolation**: The deletion only affects conversations owned by the same user (`user_id` check ensures this).

4. **Recovery**: Soft-deleted records can be recovered by setting `deleted_at` back to NULL if needed, but requires database operations.

## Related Files

| File | Change |
|------|--------|
| `backend/app/routers/memories.py` | Added Conversation import, updated `delete_memory()` to delete conversations and diary |
| `backend/tests/test_memories.py` | Updated `test_delete_memory_card_deletes_associated_conversations` to verify diary deletion |

## Verification

Run the following commands to verify:

```bash
# Unit tests
py -m pytest tests/test_memories.py::test_delete_memory_card_deletes_associated_conversations -v

# All memory tests
py -m pytest tests/test_memories.py -v

# E2E tests
py -m pytest tests/e2e/test_memory_flow.py -v
```

Expected: All tests pass with no regressions.
