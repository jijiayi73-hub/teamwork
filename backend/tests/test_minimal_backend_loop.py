from datetime import date
from pathlib import Path
import sys

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.database import Base, get_db
from app.main import app


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db
client = TestClient(app)


def setup_function():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


def register(email="user@example.com", role="user"):
    response = client.post(
        "/api/v1/auth/register",
        json={"username": email.split("@")[0], "email": email, "password": "secret123", "role": role},
    )
    assert response.status_code == 201
    return response.json()["data"]["access_token"]


def test_health_and_user_diary_stats_loop():
    token = register()
    headers = {"Authorization": f"Bearer {token}"}

    entry_response = client.post(
        "/api/v1/entries",
        json={"raw_content": "今天考试压力很大，有点焦虑，但是写下来以后平静了一点。"},
        headers=headers,
    )
    assert entry_response.status_code == 201
    entry = entry_response.json()["data"]
    assert entry["status"] == "analyzed"
    assert entry["analysis"]["primary_emotion"] in {"anxiety", "sadness", "calm", "neutral"}

    diary_response = client.post(
        "/api/v1/diaries",
        json={
            "entry_id": entry["id"],
            "title": entry["draft_title"],
            "content": entry["draft_content"],
            "diary_date": date.today().isoformat(),
            "is_favorite": True,
        },
        headers=headers,
    )
    assert diary_response.status_code == 201
    diary = diary_response.json()["data"]
    assert diary["entry_id"] == entry["id"]

    list_response = client.get("/api/v1/diaries", headers=headers)
    assert list_response.status_code == 200
    assert len(list_response.json()["data"]) == 1

    overview_response = client.get("/api/v1/stats/overview", headers=headers)
    assert overview_response.status_code == 200
    assert overview_response.json()["data"]["total_diaries"] == 1


def test_admin_stats_are_role_protected():
    user_token = register("normal@example.com")
    forbidden = client.get("/api/v1/admin/stats", headers={"Authorization": f"Bearer {user_token}"})
    assert forbidden.status_code == 403

    admin_token = register("admin@example.com", role="admin")
    response = client.get("/api/v1/admin/stats", headers={"Authorization": f"Bearer {admin_token}"})
    assert response.status_code == 200
    assert response.json()["data"]["total_users"] == 2
