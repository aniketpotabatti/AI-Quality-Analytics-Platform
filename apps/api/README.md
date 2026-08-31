# HAS API

FastAPI application for Hallucination Analytics Studio.

See the [root README](../../README.md) for setup instructions.

## Database migrations

```bash
# Apply migrations (requires DATABASE_URL in env / .env)
uv run alembic upgrade head

# Autogenerate a new revision after model changes
uv run alembic revision --autogenerate -m "describe change"
```

Schema docs: [docs/architecture/database-schema.md](../../docs/architecture/database-schema.md)

