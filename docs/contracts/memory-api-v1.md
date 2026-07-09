# Memory API Contract

Version: 1.0
Status: IMPLEMENTED
Effective date: 2026-07-08

Base path: `/api/v1`

All endpoints require `Authorization: Bearer <access_token>` except static uploaded file reads under `/uploads/...`.

## Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| POST | `/uploads/images` | Persist an uploaded image from a JSON data URL and return a static `/uploads/...` URL |
| POST | `/memories` | Create an independent memory card for a user-owned diary |
| GET | `/memories` | List current user's memory cards, optionally filtered by `emotion` and `keyword` |
| GET | `/memories/{memory_id}` | Read one current-user memory card with diary snapshot |
| PATCH | `/memories/{memory_id}` | Update card cover, emotion, color, keywords, or summary |
| DELETE | `/memories/{memory_id}` | Soft-delete a memory card |
| POST | `/memories/{memory_id}/past-self-chat` | Send a Past Self message anchored to the memory card diary |
| GET | `/admin/stats/charts` | Admin-only chart data for service status, 7-day additions, and emotion distribution |

## Upload Request

```json
{
  "filename": "cover.png",
  "content_type": "image/png",
  "data_url": "data:image/png;base64,..."
}
```

The backend accepts JPEG, PNG, WebP, and GIF, limits payloads to 4MB decoded bytes, writes files under `backend/data/uploads`, and exposes them through `/uploads/{stored_filename}`.

## Memory Create Request

```json
{
  "diary_id": 1,
  "cover_image_url": "/uploads/1-cover.png",
  "cover_prompt": "Soft watercolor garden cover...",
  "emotion_label": "calm",
  "emotion_color": "#8fb8ff",
  "keywords": ["calm", "today", "memory"],
  "conversation_summary": "AI/user transcript summary"
}
```

`diary_id` must belong to the current user. Only one active memory card may exist for one diary.

## Memory Response

```json
{
  "id": 10,
  "diary_id": 1,
  "title": "Today",
  "excerpt": "First 180 chars...",
  "diary_date": "2026-07-08",
  "cover_image_url": "/uploads/1-cover.png",
  "cover_prompt": "Soft watercolor garden cover...",
  "emotion_label": "calm",
  "emotion_color": "#8fb8ff",
  "keywords": ["calm", "today"],
  "conversation_summary": "AI/user transcript summary",
  "created_at": "2026-07-08T14:00:00Z",
  "updated_at": "2026-07-08T14:00:00Z",
  "diary": {
    "id": 1,
    "title": "Today",
    "content": "Full private diary body",
    "diary_date": "2026-07-08",
    "created_at": "2026-07-08T14:00:00Z",
    "updated_at": "2026-07-08T14:00:00Z",
    "analysis": {}
  }
}
```

## Past Self Request

```json
{
  "message": "那天的我想提醒我什么？",
  "conversation_id": null
}
```

When `conversation_id` is null, the backend creates a `past_self` chat conversation anchored to the memory card diary. When it is present, the backend continues that conversation.

## Admin Chart Response

`GET /admin/stats` remains backward-compatible and returns integer counters only. `GET /admin/stats/charts` returns counters plus:

- `daily_new_memory_cards`
- `emotion_distribution`
- `service_status`
- `privacy_note`
