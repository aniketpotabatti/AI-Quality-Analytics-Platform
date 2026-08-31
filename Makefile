.PHONY: install api-install web-install engine-install \
        api-dev web-dev worker-dev \
        test test-api test-engine test-web \
        lint lint-api lint-engine lint-web \
        format migrate migrate-down migrate-history migrate-revision

# ── Install ──────────────────────────────────────────────────────────────────

install: api-install engine-install web-install

api-install:
	cd apps/api && uv sync --dev

engine-install:
	cd packages/evaluation-engine && uv sync --dev

web-install:
	cd apps/web && npm install

# ── Development ──────────────────────────────────────────────────────────────

api-dev:
	cd apps/api && uv run uvicorn has_api.main:app --reload --host 0.0.0.0 --port 8000

web-dev:
	cd apps/web && npm run dev

worker-dev:
	cd apps/api && uv run arq has_api.workers.settings.WorkerSettings

# ── Test ─────────────────────────────────────────────────────────────────────

test: test-api test-engine test-web

test-api:
	cd apps/api && uv run pytest

test-engine:
	cd packages/evaluation-engine && uv run pytest

test-web:
	cd apps/web && npm run test

# ── Lint ─────────────────────────────────────────────────────────────────────

lint: lint-api lint-engine lint-web

lint-api:
	cd apps/api && uv run ruff check . && uv run mypy src

lint-engine:
	cd packages/evaluation-engine && uv run ruff check . && uv run mypy src

lint-web:
	cd apps/web && npm run lint

# ── Format ───────────────────────────────────────────────────────────────────

format:
	cd apps/api && uv run ruff format .
	cd packages/evaluation-engine && uv run ruff format .

# ── Database (Milestone 2+) ──────────────────────────────────────────────────

migrate:
	cd apps/api && uv run alembic upgrade head

migrate-down:
	cd apps/api && uv run alembic downgrade -1

migrate-history:
	cd apps/api && uv run alembic history --verbose

# Usage: make migrate-revision MSG="add index on foo"
migrate-revision:
	cd apps/api && uv run alembic revision --autogenerate -m "$(MSG)"
