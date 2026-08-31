"""API test suite."""

import os

# Minimal env vars required by Settings before app import in tests.
os.environ.setdefault("APP_SECRET_KEY", "test-secret-key-with-sufficient-length")
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://has:has@localhost:5432/hallucination_analytics_test",
)
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/1")
os.environ.setdefault("JWT_SECRET_KEY", "test-jwt-secret-key-with-sufficient-length")
