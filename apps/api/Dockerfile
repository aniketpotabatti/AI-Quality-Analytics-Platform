FROM python:3.12-slim

# Install uv for fast dependency resolution and build tools for packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install uv

WORKDIR /app

# Copy the workspace root packages
COPY packages/ ./packages/

WORKDIR /app/apps/api

# Copy API dependencies and install
COPY apps/api/pyproject.toml apps/api/uv.lock ./
# Note: Since the evaluation-engine package is a path dependency, we need to ensure the path resolves correctly. 
# We've copied it to /app/packages, and we are in /app/apps/api, so ../../packages/evaluation-engine works.

RUN uv pip install --system -e .
RUN uv pip install --system -e ../../packages/evaluation-engine

# Copy application code
COPY apps/api/src/ ./src/
COPY apps/api/alembic/ ./alembic/
COPY apps/api/alembic.ini ./

ENV PYTHONPATH=/app/apps/api/src:/app/packages/evaluation-engine/src

EXPOSE 8000

CMD ["uvicorn", "has_api.main:app", "--host", "0.0.0.0", "--port", "8000"]
