"""
テスト用フィクスチャ
- インメモリ SQLite を使用（本番DBに影響しない）
- 認証済みクライアントのファクトリ
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.database import Base, get_db
from app.main import app

TEST_DB_URL = "sqlite:///./test_memorial.db"

engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    try:
        os.remove("test_memorial.db")
    except FileNotFoundError:
        pass


@pytest.fixture(scope="function")
def db():
    app.dependency_overrides[get_db] = override_get_db
    db = TestingSessionLocal()
    yield db
    db.rollback()
    db.close()
    # テーブルを空にして各テストを独立させる
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def client(db):
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def auth_client(client):
    """登録済みユーザーでログイン済みのクライアント"""
    client.post("/api/auth/register", json={
        "name": "テストユーザー",
        "email": "test@example.com",
        "password": "password123",
    })
    res = client.post("/api/auth/login", data={
        "username": "test@example.com",
        "password": "password123",
    })
    token = res.json()["access_token"]
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client


@pytest.fixture(scope="function")
def second_auth_client(client):
    """別ユーザー（認可テスト用）"""
    client.post("/api/auth/register", json={
        "name": "別ユーザー",
        "email": "other@example.com",
        "password": "password456",
    })
    res = client.post("/api/auth/login", data={
        "username": "other@example.com",
        "password": "password456",
    })
    token = res.json()["access_token"]
    other = TestClient(app)
    other.headers.update({"Authorization": f"Bearer {token}"})
    return other
