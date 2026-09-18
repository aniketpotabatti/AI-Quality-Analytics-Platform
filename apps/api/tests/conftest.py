"""Real end-to-end auth tests against SQLite (no Postgres/Redis needed)."""

import os

os.environ.setdefault("APP_SECRET_KEY", "test-secret-key-with-sufficient-length")
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret-key-with-sufficient-length")

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from has_api.infrastructure.database import session as session_module
from has_api.infrastructure.database.base import Base
from has_api.infrastructure.database.session import get_db_session


@pytest.fixture
async def client(tmp_path, monkeypatch) -> AsyncClient:
    db_url = f"sqlite+aiosqlite:///{tmp_path}/test.db"
    monkeypatch.setenv("DATABASE_URL", db_url)

    from has_api.config import settings as settings_module

    settings_module.get_settings.cache_clear()
    session_module.reset_engine()

    # Import models so metadata is populated before create_all.
    import has_api.infrastructure.database.models  # noqa: F401

    engine = create_async_engine(db_url)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    test_factory = async_sessionmaker(bind=engine, expire_on_commit=False)

    async def override_session():
        async with test_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise

    from has_api.main import app

    app.dependency_overrides[get_db_session] = override_session
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()
    await engine.dispose()
    session_module.reset_engine()
    settings_module.get_settings.cache_clear()


@pytest.mark.asyncio
async def test_register_login_me_flow(client: AsyncClient) -> None:
    email = "e2e@example.com"
    register = await client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "password": "password123",
            "full_name": "E2E User",
            "workspace_name": "E2E Workspace",
        },
    )
    assert register.status_code == 201, register.text
    tokens = register.json()
    assert tokens["access_token"]
    assert tokens["refresh_token"]

    login = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "password123"},
    )
    assert login.status_code == 200, login.text

    me = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {login.json()['access_token']}"},
    )
    assert me.status_code == 200, me.text
    body = me.json()
    assert body["user"]["email"] == email
    assert len(body["workspaces"]) == 1


@pytest.mark.asyncio
async def test_register_duplicate_email_returns_409(client: AsyncClient) -> None:
    payload = {
        "email": "dup@example.com",
        "password": "password123",
        "full_name": "Dup",
        "workspace_name": "WS",
    }
    first = await client.post("/api/v1/auth/register", json=payload)
    assert first.status_code == 201, first.text
    second = await client.post("/api/v1/auth/register", json=payload)
    assert second.status_code == 409


@pytest.mark.asyncio
async def test_login_wrong_password_returns_401(client: AsyncClient) -> None:
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "wrong@example.com",
            "password": "password123",
            "full_name": "Wrong",
            "workspace_name": "WS",
        },
    )
    bad = await client.post(
        "/api/v1/auth/login",
        json={"email": "wrong@example.com", "password": "nope-nope-nope"},
    )
    assert bad.status_code == 401

