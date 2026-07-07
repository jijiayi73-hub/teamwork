from fastapi import FastAPI

from . import models
from .database import Base, engine
from .routers import admin, auth, diaries, entries, stats

Base.metadata.create_all(bind=engine)

app = FastAPI(title="InnerGarden API")

app.include_router(auth.router, prefix="/api/v1")
app.include_router(entries.router, prefix="/api/v1")
app.include_router(diaries.router, prefix="/api/v1")
app.include_router(stats.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/api/v1/health")
def api_health_check():
    return {"status": "ok"}
