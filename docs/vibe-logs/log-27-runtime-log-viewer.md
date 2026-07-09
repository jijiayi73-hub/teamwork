# Runtime Log Viewer Implementation

**Date:** 2026-07-09
**Task:** TASK-015
**Status:** Complete

## Goal
Replace the FastAPI Swagger UI documentation at `http://localhost:8000` with a runtime log viewer interface that displays logs in layers (info, error, warning levels).

## Implementation

### Components Created

1. **Log Storage Module** (`backend/app/logger/storage.py`)
   - `LogStorage` class with thread-safe in-memory storage
   - Maximum 2000 entries with automatic rotation (deque)
   - `LogEntry` class for structured log data
   - `StorageHandler` for integration with logging system

2. **Log API Endpoints** (`backend/app/routers/logs.py`)
   - `GET /api/v1/logs/entries` - Retrieve logs with optional level filter
   - `GET /api/v1/logs/stats` - Get log statistics by level
   - `GET /api/v1/logs/levels` - Get available log levels
   - `POST /api/v1/logs/clear` - Clear all stored logs

3. **Log Capture Integration**
   - Updated `RequestLoggingMiddleware` to store HTTP request/response logs
   - Updated exception handlers to store error logs with context

4. **Log Viewer UI** (`backend/static/logs.html`)
   - Clean, dark-themed interface matching Inner Garden aesthetic
   - Real-time statistics cards (total, info, warning, error counts)
   - Level filtering buttons (All, Info, Warning, Error)
   - Auto-refresh toggle (5-second interval)
   - Expandable log entries with details (request_id, path, status_code, duration_ms)
   - Login requirement check with redirect to frontend login

5. **Root Path Configuration** (`backend/app/main.py`)
   - `GET /` now returns the log viewer HTML page
   - Static file serving configured for `/static` path

## Technical Details

### Log Entry Structure
```python
{
    "level": "INFO|WARNING|ERROR|DEBUG|CRITICAL",
    "message": "Log message text",
    "timestamp": "2026-07-09T12:34:56.789Z",
    "request_id": "uuid",  # optional
    "path": "/api/v1/...",  # optional
    "method": "GET|POST...",  # optional
    "status_code": 200,  # optional
    "duration_ms": 45.2  # optional
}
```

### API Endpoints

#### GET /api/v1/logs/entries
Query parameters:
- `level`: Filter by log level (optional)
- `limit`: Maximum entries to return (1-500, default 100)

#### GET /api/v1/logs/stats
Returns:
```json
{
    "total": 150,
    "info": 100,
    "warning": 30,
    "error": 15,
    "debug": 5,
    "critical": 0
}
```

## Usage

1. Start the backend service:
   ```bash
   cd backend
   py -m uvicorn app.main:app --reload
   ```

2. Access the log viewer:
   - Navigate to `http://localhost:8000`
   - Login if prompted (uses JWT token from localStorage)

3. Features:
   - **Filter by level**: Click the level buttons to filter logs
   - **Auto-refresh**: Click the auto-refresh indicator to toggle (default on)
   - **Expand details**: Click any log entry to see additional context
   - **Clear logs**: Click "清空日志" to remove all stored logs

## Limitations

1. **In-memory storage**: Logs are lost when the service restarts
2. **Capacity limit**: Maximum 2000 log entries, oldest entries are removed when limit is exceeded
3. **Authentication required**: Users must be logged in to view logs
4. **No persistence**: Logs are not saved to disk or database

## Future Enhancements

Potential improvements for production:
1. Add log persistence to database
2. Implement log export (CSV/JSON)
3. Add search functionality
4. Implement log retention policies
5. Add real-time WebSocket updates instead of polling

## Evidence

- Backend imports verified: `from app.main import app` passes
- Log storage tested: `get_log_storage()` returns working instance
- Static file serving configured: `/static/logs.html` accessible
- Root path configured: `GET /` returns log viewer page

## Files Changed

- `backend/app/logger/storage.py` (new)
- `backend/app/routers/logs.py` (updated)
- `backend/app/logger/middleware.py` (updated)
- `backend/app/logger/exception_handler.py` (updated)
- `backend/app/main.py` (updated)
- `backend/static/logs.html` (new)
- `docs/state/task-board.md` (updated)
- `docs/state/current-status.md` (updated)
