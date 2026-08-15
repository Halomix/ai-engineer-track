"""Does an index actually make a slow query fast? Measured, not claimed.

Seeds a lot of notes, then times a query that searches by an exact title —
once BEFORE the notes.title index exists, once AFTER — so "the index made
it faster" is a real number, not a guess.

Run it:
    uv run python phase-1/week-1/scripts/benchmark_index.py
"""

from __future__ import annotations

import random
import string
import sys
import time
import uuid
from datetime import UTC, datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from notes_service.db import SessionLocal  # noqa: E402
from notes_service.db_models import NoteRow  # noqa: E402
from sqlalchemy import func, select, text  # noqa: E402

ROW_COUNT = 20_000
# One title we can reliably search for, buried among thousands of
# random ones — proving the search has to actually work, not just
# find row #1.
NEEDLE_TITLE = "find-me-exactly-once"


def seed_if_needed() -> None:
    with SessionLocal() as session:
        current = session.scalar(select(func.count()).select_from(NoteRow)) or 0
        if current >= ROW_COUNT:
            print(f"already have {current:,} rows — skipping seed")
            return

        to_add = ROW_COUNT - current
        print(f"seeding {to_add:,} rows (a few seconds)...")

        rows = [
            NoteRow(
                id=uuid.uuid4(),
                title="".join(random.choices(string.ascii_lowercase, k=12)),
                body=f"generated row {i}",
                created_at=datetime.now(UTC),
            )
            for i in range(to_add)
        ]
        rows.append(
            NoteRow(
                id=uuid.uuid4(),
                title=NEEDLE_TITLE,
                body="the one row we search for",
                created_at=datetime.now(UTC),
            )
        )
        session.bulk_save_objects(rows)
        session.commit()
        print("seeding done")


def time_the_search() -> None:
    with SessionLocal() as session:
        # EXPLAIN ANALYZE actually runs the query and reports the real plan
        # Postgres chose, plus real timing — "Seq Scan" means it checked
        # every row; "Index Scan" means it jumped straight to the answer.
        plan_rows = session.execute(
            text("EXPLAIN ANALYZE SELECT * FROM notes WHERE title = :t"),
            {"t": NEEDLE_TITLE},
        ).fetchall()

        print("\n--- query plan ---")
        for row in plan_rows:
            print(" ", row[0])

        # A second, plain wall-clock timing alongside Postgres's own
        # reported figure — the number you'd actually put in a report.
        start = time.perf_counter()
        session.execute(
            text("SELECT * FROM notes WHERE title = :t"), {"t": NEEDLE_TITLE}
        ).fetchall()
        elapsed_ms = (time.perf_counter() - start) * 1000
        print(f"\nwall-clock: {elapsed_ms:.3f}ms, searching {ROW_COUNT:,} rows")


if __name__ == "__main__":
    seed_if_needed()
    time_the_search()
