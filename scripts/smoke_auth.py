"""Smoke-test the register/login flow against the real app (SQLite dev DB)."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "apps" / "api" / "src"))

from httpx import ASGITransport, AsyncClient  # noqa: E402

from has_api.main import app  # noqa: E402


async def main() -> None:
    from has_api.infrastructure.database import init_db

    await init_db()  # lifespan-equivalent: ASGITransport doesn't run lifespan
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        email = "smoke@example.com"
        reg = await client.post(
            "/api/v1/auth/register",
            json={
                "email": email,
                "password": "password123",
                "full_name": "Smoke User",
                "workspace_name": "Smoke WS",
            },
        )
        print("register:", reg.status_code, reg.text[:200])
        assert reg.status_code == 201, reg.text

        login = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "password123"},
        )
        print("login:", login.status_code, login.text[:200])
        assert login.status_code == 200, login.text

        me = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {login.json()['access_token']}"},
        )
        print("me:", me.status_code, me.text[:300])
        assert me.status_code == 200, me.text
        print("SMOKE OK — register/login/me all work")


asyncio.run(main())
