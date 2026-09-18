# AI Quality Analytics Platform

A production-grade platform for evaluating LLM outputs against hallucination, faithfulness, and grounding metrics. Built as a portfolio project with SaaS-shaped architecture: modular monolith, domain-driven design, and a pluggable evaluation engine.

**Created:** April 2026

## Vision

Teams use Hallucination Analytics Studio to:

- **Ingest** datasets of prompts, responses, context, and ground truth
- **Run** batch evaluations with configurable metrics and detectors
- **Analyze** hallucination rates, failure modes, and model comparisons
- **Iterate** as prompts, models, and RAG pipelines evolve

## Architecture

```
apps/
  api/                    FastAPI application (HTTP + orchestration)
  web/                    Next.js dashboard
packages/
  evaluation-engine/      Pure Python evaluation library
docs/
  adr/                    Architecture Decision Records
infrastructure/
  docker/                 Container definitions (Milestone 8)
```

See [docs/adr/001-monorepo-and-layered-architecture.md](docs/adr/001-monorepo-and-layered-architecture.md) for design rationale.

## Tech Stack


| Layer    | Technology                                    |
| -------- | --------------------------------------------- |
| API      | Python 3.12, FastAPI, SQLAlchemy 2, Alembic   |
| Engine   | Pure Python package (Pydantic v2)             |
| Database | PostgreSQL 16                                 |
| Jobs     | Redis + ARQ                                   |
| Frontend | Next.js 15, TypeScript, Tailwind CSS          |
| Auth     | JWT (access + refresh), workspace-scoped RBAC |


## Prerequisites

- Python 3.12+
- Node.js 20+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip
- PostgreSQL 16 + Redis 7 — only for production-like runs / Docker Compose.
  Local dev works with zero extra services (SQLite dev.db + no Redis).

## Quick Start

```bash
# Copy environment template
cp .env.example .env

# Install all dependencies
make install          # Linux/macOS
# or: .\scripts\dev.ps1 install   # Windows PowerShell

# Run API (development) — no Postgres/Redis needed
make api-dev          # serves http://localhost:8000 (SQLite dev.db auto-created)

# Run web (development, separate terminal)
make web-dev          # open http://localhost:3000/login to register/login

# Run tests
make test

# Lint
make lint
```

### Troubleshooting "Failed to fetch" on login/register

That message means the browser could not reach the API at all (it never got
an HTTP status back). Check in order:

1. API running? Open `http://localhost:8000/health` — expect `{"status":"ok",...}`.
2. Same `NEXT_PUBLIC_API_URL` as the API? Default `http://localhost:8000`.
   After changing it, restart `npm run dev` (Next.js bakes the value in at startup).
3. Wrong port / mixed hosts? Use `localhost` consistently (`127.0.0.1` vs
   `localhost` can trigger CORS or cookie issues in some browsers).
4. API crashed on startup? Look at the `make api-dev` terminal for the error.
   Common past causes (all fixed): `API_CORS_ORIGINS` env parsing,
   passlib/bcrypt version mismatch, missing Postgres/Redis.
```

## Project Structure (API layers)

Within `apps/api/src/`:


| Layer             | Purpose                                    |
| ----------------- | ------------------------------------------ |
| `api/`            | HTTP routers, request/response DTOs        |
| `application/`    | Use cases and orchestration                |
| `domain/`         | Entities, value objects, domain exceptions |
| `infrastructure/` | Database, Redis, external clients          |
| `workers/`        | Async job definitions                      |


## License

MIT (portfolio use)