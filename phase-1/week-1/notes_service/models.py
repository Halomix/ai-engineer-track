"""Pydantic models — the shapes of data crossing the service boundary.

Anything coming IN from a caller is checked against a model before any of
our own code touches it. Anything going OUT is shaped by a model too, so
every caller gets a predictable, documented structure back.

This file is the border checkpoint for the whole service.
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class NoteCreate(BaseModel):
    """What a caller must send to create a note.

    Nothing gets past this model without a real title and a real body.
    That check happens automatically, before create_note() in main.py
    ever runs.
    """

    title: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1, max_length=10_000)

    @field_validator("title", "body")
    @classmethod
    def reject_whitespace_only(cls, value: str) -> str:
        """ "   " passes a min_length check but means nothing. Catch it here
        so it never reaches storage as a "valid" but useless note."""
        stripped = value.strip()
        if not stripped:
            raise ValueError("cannot be empty or only whitespace")
        return stripped


class Note(BaseModel):
    """A note as stored and returned.

    Note: a caller can never set `id` or `created_at` themselves — those
    fields don't exist on NoteCreate above. The server decides them. This
    is deliberate: letting a client pick its own ID invites collisions and
    spoofing; letting it pick its own timestamp invites lies.
    """

    id: UUID = Field(default_factory=uuid4)
    title: str
    body: str
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))


class NoteList(BaseModel):
    """Response shape for listing notes.

    `total` is the full count even when `items` is a smaller page — a
    caller can tell "there are 500 notes, I have 50" without a second
    request just to count.
    """

    items: list[Note]
    total: int
