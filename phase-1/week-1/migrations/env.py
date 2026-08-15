"""Alembic environment.

This connects Alembic to two things:

1. Your real database connection (read from .env — same source the
   running app uses, so migrations and the app can never disagree about
   which database they're talking to).
2. Your actual schema, as defined in Python in db_models.py.

`alembic revision --autogenerate` compares those two: what the code says
the schema should be, against what the database actually has right now —
and writes a migration file describing the difference.
"""

from __future__ import annotations

import os
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from dotenv import load_dotenv
from sqlalchemy import engine_from_config, pool

# migrations/env.py needs to import notes_service, which lives one folder
# up from here — this line makes that import possible.
sys.path.insert(0, str(Path(__file__).parent.parent))

from notes_service.db_models import Base  # noqa: E402

load_dotenv()

config = context.config

# Read the connection string from .env instead of hardcoding it in
# alembic.ini. One source of truth for "where is the database" — the same
# one notes_service/db.py uses.
config.set_main_option("sqlalchemy.url", os.environ["DATABASE_URL"])

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# This is the piece that makes --autogenerate work: it diffs the real
# database against everything defined in db_models.py.
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Generates SQL without connecting to a database — used to produce a
    .sql file for someone else to run by hand. Not used day-to-day here,
    but it's the standard escape hatch when you can't connect directly."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """The normal path: connect for real and apply migrations directly."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
