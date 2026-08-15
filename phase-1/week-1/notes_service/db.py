"""Database connection setup — the one place that knows how to talk to Postgres.

Everything below configures a CONNECTION POOL: instead of opening a brand
new connection to Postgres for every request (slow, and Postgres has a
hard limit on how many connections it accepts at once), we keep a small
number open and ready, and each request borrows one and hands it back.

This is invisible when it works and the cause of real production outages
when it's missing — "FATAL: too many connections" is one of the most
common ways a database-backed service goes down under load.
"""

from __future__ import annotations

import os

from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

# Loaded once, here, so every module that imports this file gets a working
# DATABASE_URL without each one having to remember to load .env itself.
load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]

engine = create_engine(
    DATABASE_URL,
    # Keep this many connections open and ready at all times.
    pool_size=5,
    # Allow up to this many EXTRA connections during a burst of traffic —
    # closed again once things calm back down.
    max_overflow=10,
    # Test a connection is actually still alive before handing it out.
    # Protects against a connection that silently died (network blip,
    # database restart) while it sat idle in the pool.
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, class_=Session)
