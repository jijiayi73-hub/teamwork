from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pathlib import Path

# Load environment variables from .env file (if exists)
# This must be done before importing config
from dotenv import load_dotenv
load_dotenv()

# Configure logging before importing other modules
from .logger.config import configure_logging
from .logger.middleware import RequestLoggingMiddleware
from .logger.exception_handler import add_exception_handlers
from .config import settings

configure_logging()

from . import models
from .routers import admin, auth, chat, diaries, entries, images, logs, memories, stats, trash
from .auth import admin as auth_admin

# Create FastAPI app with admin-only OpenAPI docs
app = FastAPI(
    title="InnerGarden API",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Static directories
upload_dir = Path(__file__).resolve().parents[1] / "data" / "uploads"
upload_dir.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(upload_dir)), name="uploads")

static_dir = Path(__file__).resolve().parents[1] / "static"
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Add CORS middleware first
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Add request logging middleware
app.add_middleware(RequestLoggingMiddleware)

# Add global exception handlers
add_exception_handlers(app)

# Include routers
app.include_router(auth.router, prefix="/api/v1")
app.include_router(entries.router, prefix="/api/v1")
app.include_router(diaries.router, prefix="/api/v1")
app.include_router(stats.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(logs.router, prefix="/api/v1")
app.include_router(chat.router, prefix="/api/v1")
app.include_router(memories.router, prefix="/api/v1")
app.include_router(trash.router, prefix="/api/v1")
app.include_router(images.router, prefix="/api/v1")


@app.get("/health")
def health_check():
    from .schemas.common import ApiResponse
    return ApiResponse(data={"status": "healthy"})


@app.get("/api/v1/health")
def api_health_check():
    from .schemas.common import ApiResponse
    return ApiResponse(data={"status": "healthy", "api_version": "v1"})


@app.get("/", response_class=FileResponse)
async def root(current_admin: models.User = Depends(auth_admin.get_current_admin)):
    """
    Serve the log viewer page at root.
    Only accessible to admin users.
    """
    logs_page = static_dir / "logs.html"
    if logs_page.exists():
        return FileResponse(str(logs_page))
    # Fallback to API docs if logs page doesn't exist
    return {"message": "InnerGarden API", "docs": "/docs", "logs": "/static/logs.html"}


# Protect API documentation endpoints
@app.get("/docs", include_in_schema=False)
async def docs_redirect():
    """Redirect to login for unauthorized users accessing docs."""
    return JSONResponse(
        status_code=401,
        content={
            "detail": "Authentication required. Please login as admin to access API documentation.",
            "login_url": "/api/v1/auth/login"
        }
    )


@app.get("/redoc", include_in_schema=False)
async def redoc_redirect():
    """Redirect to login for unauthorized users accessing redoc."""
    return JSONResponse(
        status_code=401,
        content={
            "detail": "Authentication required. Please login as admin to access API documentation.",
            "login_url": "/api/v1/auth/login"
        }
    )


@app.get("/openapi.json", include_in_schema=False)
async def openapi(current_admin: models.User = Depends(auth_admin.get_current_admin)):
    """Serve OpenAPI schema only to admin users."""
    from fastapi.openapi.utils import get_openapi
    return get_openapi(
        title=app.title,
        version="1.0.0",
        routes=app.routes,
    )
