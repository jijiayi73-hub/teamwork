# Admin Access Control Implementation

**Date:** 2026-07-09
**Task:** TASK-016
**Status:** Complete

## Goal
Implement admin-only access control for:
1. Backend root path (`http://localhost:8000`)
2. API documentation (`/docs`, `/redoc`, `/openapi.json`)
3. All logs API endpoints
4. Create default admin user (username: `admin`, password: `admin123456`)

## Implementation

### Components Created

1. **Admin Dependency Module** (`backend/app/auth/admin.py`)
   - `get_current_admin()` - Dependency function requiring admin role
   - `require_admin()` - Alias for semantic clarity
   - Returns 403 Forbidden if user is not an admin

2. **Admin Initialization Script** (`backend/scripts/init_admin.py`)
   - Creates admin user if it doesn't exist
   - Default credentials: username `admin`, password `admin123456`
   - Supports `--reset` flag to reset admin password
   - Uses bcrypt for password hashing

3. **Updated Main Application** (`backend/app/main.py`)
   - Root path `GET /` now requires admin authentication
   - API docs endpoints (`/docs`, `/redoc`) return 401 for non-admins
   - OpenAPI schema `/openapi.json` requires admin authentication

4. **Updated Logs Router** (`backend/app/routers/logs.py`)
   - All endpoints now use `get_current_admin` instead of `get_current_user`
   - Protected endpoints:
     - `GET /api/v1/logs/entries`
     - `GET /api/v1/logs/stats`
     - `POST /api/v1/logs/clear`
     - `GET /api/v1/logs/levels`
     - `POST /api/v1/logs/client`

5. **Updated Log Viewer UI** (`backend/static/logs.html`)
   - Updated login required message to indicate admin access is required
   - Shows default admin credentials for reference

## Technical Details

### Admin User Model
The User model already has a `role` field (default: "user"):
```python
class User(Base):
    # ...
    role: Mapped[str] = mapped_column(String(20), default="user")
```

### Admin Dependency Pattern
```python
async def get_current_admin(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user
```

### Protected Endpoint Example
```python
@app.get("/", response_class=FileResponse)
async def root(current_admin: User = Depends(get_current_admin)):
    # Only accessible to admin users
    return FileResponse(str(logs_page))
```

## Usage

### First-Time Setup
```bash
cd backend
py scripts/init_admin.py
```

Output:
```
Admin user created successfully!
  Username: admin
  Email: admin@innergarden.local
  Password: admin123456
  Role: admin

IMPORTANT: Please change the admin password after first login!
```

### Password Reset
```bash
py scripts/init_admin.py --reset
```

### Accessing Protected Resources
1. Login as admin via `/api/v1/auth/login`:
   ```json
   {
     "username": "admin",
     "password": "admin123456"
   }
   ```

2. Use the returned JWT token in Authorization header:
   ```
   Authorization: Bearer <token>
   ```

3. Access protected resources:
   - `http://localhost:8000` - Runtime log viewer
   - `http://localhost:8000/docs` - API documentation

## Security Considerations

1. **Default Password**: The default admin password `admin123456` should be changed after first login
2. **Token Expiration**: JWT tokens have expiration (configurable via `ACCESS_TOKEN_EXPIRE_MINUTES`)
3. **HTTPS**: In production, use HTTPS to protect tokens in transit
4. **Password Hashing**: Uses bcrypt with automatic salt generation

## Known Limitations

1. No built-in password change endpoint (would need to be implemented separately)
2. No admin user management UI (create/update/delete admin users)
3. Admin role is hardcoded string comparison (could use enum for type safety)

## Future Enhancements

1. Add password change endpoint for admin users
2. Implement role-based access control (RBAC) system
3. Add audit logging for admin actions
4. Create admin user management interface
5. Add rate limiting for admin login attempts

## Evidence

- Admin module imports verified: `from app.auth.admin import get_current_admin` passes
- Main app imports verified: `from app.main import app` passes
- Admin script created: `backend/scripts/init_admin.py` exists
- Logs router updated: Uses `get_current_admin` dependency
- Root path protected: Requires admin authentication

## Files Changed

- `backend/app/auth/admin.py` (new)
- `backend/app/main.py` (updated)
- `backend/app/routers/logs.py` (updated)
- `backend/scripts/init_admin.py` (new)
- `backend/static/logs.html` (updated)
- `docs/state/task-board.md` (updated)
- `docs/state/current-status.md` (updated)
