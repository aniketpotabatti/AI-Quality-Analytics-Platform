# AI Quality Analytics Platform

A production-grade platform for evaluating LLM outputs against hallucination, faithfulness, and grounding metrics. Built as a portfolio project with SaaS-shaped architecture: modular monolith, domain-driven design, and a pluggable evaluation engine.

**Created:** April 2026

## Vision

Teams use AI Quality Analytics Platform to:

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

| Layer | Technology |
|-------|------------|
| API | Python 3.12, FastAPI, SQLAlchemy 2, Alembic |
| Engine | Pure Python package (Pydantic v2) |
| Database | PostgreSQL 16 |
| Jobs | Redis + ARQ |
| Frontend | Next.js 15, TypeScript, Tailwind CSS |
| Auth | JWT (access + refresh), workspace-scoped RBAC |

## Prerequisites

- Python 3.12+
- Node.js 20+
- PostgreSQL 16
- Redis 7
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

## Quick Start

```bash
# Copy environment template
cp .env.example .env

# Install all dependencies
make install          # Linux/macOS
# or: .\scripts\dev.ps1 install   # Windows PowerShell

# Run API (development)
make api-dev

# Run web (development, separate terminal)
make web-dev

# Run tests
make test

# Lint
make lint
```

## Project Structure (API layers)

Within `apps/api/src/`:

| Layer | Purpose |
|-------|---------|
| `api/` | HTTP routers, request/response DTOs |
| `application/` | Use cases and orchestration |
| `domain/` | Entities, value objects, domain exceptions |
| `infrastructure/` | Database, Redis, external clients |
| `workers/` | Async job definitions |

## License

MIT (portfolio use)
