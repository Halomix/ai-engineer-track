"""SQLAlchemy table definitions — the real database schema, as Python.

This file is the single source of truth for what the `notes` table looks
like. Alembic reads it to generate migrations; storage.py reads it to
query and save rows. Nothing else defines what a note looks like in the
database.

This is deliberately a separate file from models.py. models.py answers
"what is a caller allowed to send us / what do we hand back" — an API
concern. This file answers "how is it actually stored" — a database
concern. Those two questions have different answers over time (a column
gets added for internal bookkeeping that the API never exposes, say), so
they get separate files rather than one doing both jobs.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, String, Text
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class NoteRow(Base):
    """The `notes` table. One row per note."""

    __tablename__ = "notes"

    id: Mapped[uuid.UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    # index=True — this single word is what scripts/benchmark_index.py
    # measures. Migration 1 created this column with no index; migration
    # 2 (below) adds one, with the timing proof taken either side of it.
    title: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
