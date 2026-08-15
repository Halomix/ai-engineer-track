"""Storage for notes — now backed by real Postgres instead of a dictionary.

Same public shape as week 1's version: create(), get(), list(), and the
same NoteNotFoundError. main.py does not change AT ALL because of this
swap — that was the whole point of keeping storage behind its own small
interface from day one.
"""

from __future__ import annotations

from collections.abc import Callable
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from notes_service.db import SessionLocal
from notes_service.db_models import NoteRow
from notes_service.models import Note


class NoteNotFoundError(Exception):
    """Raised when a note id doesn't exist.

    Storage code should never know about HTTP status codes — that's a web
    concern. main.py is the layer that turns this into a proper 404.
    """


class NoteStore:
    def __init__(self, session_factory: Callable[[], Session] = SessionLocal) -> None:
        self._session_factory = session_factory

    def create(self, note: Note) -> Note:
        with self._session_factory() as session:
            row = NoteRow(id=note.id, title=note.title, body=note.body, created_at=note.created_at)
            session.add(row)
            session.commit()
        return note

    def get(self, note_id: UUID) -> Note:
        with self._session_factory() as session:
            row = session.get(NoteRow, note_id)
            if row is None:
                raise NoteNotFoundError(f"no note with id {note_id}")
            return Note(id=row.id, title=row.title, body=row.body, created_at=row.created_at)

    def list(self, limit: int = 50, offset: int = 0) -> tuple[list[Note], int]:
        with self._session_factory() as session:
            total = session.scalar(select(func.count()).select_from(NoteRow)) or 0
            rows = session.scalars(
                select(NoteRow).order_by(NoteRow.created_at.desc()).limit(limit).offset(offset)
            ).all()
            items = [
                Note(id=r.id, title=r.title, body=r.body, created_at=r.created_at) for r in rows
            ]
            return items, total
