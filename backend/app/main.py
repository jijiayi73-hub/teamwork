from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Configure logging before importing other modules
from .logger.config import configure_logging
from .logger.middleware import RequestLoggingMiddleware
from .logger.exception_handler import add_exception_handlers

configure_logging()

from . import models
from .database import Base, engine
from .routers import admin, auth, diaries, entries, logs, stats

Base.metadata.create_all(bind=engine)

app = FastAPI(title="InnerGarden API")

# Add CORS middleware first
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:5175", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
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


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/api/v1/health")
def api_health_check():
    return {"status": "ok"}
