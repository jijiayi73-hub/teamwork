# Backend

Backend workspace for the CampusProject application.

## Suggested Commands

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Directory Guide

- `app/main.py`: application entry point
- `app/config.py`: runtime configuration
- `app/database.py`: database connection helpers
- `app/models/`: database models
- `app/schemas/`: request and response schemas
- `app/routers/`: API routes
- `app/services/`: business logic
- `app/auth/`: authentication and authorization logic
- `app/utils/`: shared backend helpers

## Database

**Database Path**: `backend/data/app.db`

The application uses SQLite with the database located at `backend/data/app.db` (relative path `./data/app.db` from the backend directory).

**Migration Management**: Alembic

- Run migrations: `py -m alembic upgrade head`
- Check current version: `py -m alembic current`
- View migration history: `py -m alembic history`

**Note**: Database files are excluded from Git via `.gitignore` (*.db pattern).

