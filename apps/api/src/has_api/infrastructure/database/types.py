"""Portable column types: Postgres-native when available, generic otherwise.

Production uses PostgreSQL (UUID + JSONB). For zero-dependency local dev
(SQLite via aiosqlite), the same models must still create tables:

- ``GUID`` — SQLAlchemy's generic ``Uuid`` renders as native ``UUID`` on
  PostgreSQL and ``CHAR(32)`` on SQLite.
- ``JSONVariant`` — native ``JSONB`` on PostgreSQL, generic ``JSON`` elsewhere.
"""

from sqlalchemy import JSON, Uuid
from sqlalchemy.dialects.postgresql import JSONB as _PG_JSONB

GUID = Uuid
JSONVariant = JSON().with_variant(_PG_JSONB(), "postgresql")

__all__ = ["GUID", "JSONVariant"]
