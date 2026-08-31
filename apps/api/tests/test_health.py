"""Tests for system health endpoints."""

import pytest
from httpx import ASGITransport, AsyncClient

from has_api.main import app


@pytest.fixture
async def client() -> AsyncClient:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_health_returns_ok(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["service"] == "has-api"
    assert "version" in body


@pytest.mark.asyncio
async def test_root_returns_service_info(client: AsyncClient) -> None:
    response = await client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert "service" in body
    assert body["docs"] == "/docs"
