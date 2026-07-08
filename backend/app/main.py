from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

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
from .routers import admin, auth, chat, diaries, entries, logs, stats

app = FastAPI(title="InnerGarden API")

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


@app.get("/health")
def health_check():
    from .schemas.common import ApiResponse
    return ApiResponse(data={"status": "healthy"})


@app.get("/api/v1/health")
def api_health_check():
    from .schemas.common import ApiResponse
    return ApiResponse(data={"status": "healthy", "api_version": "v1"})
