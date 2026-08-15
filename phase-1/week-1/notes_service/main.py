"""The Notes service.

Three endpoints, on purpose kept small: create a note, fetch one, list
them. The point of week 1 is proving every quality below works on
something simple — not building something impressive.

Run it:
    uv run uvicorn notes_service.main:app --app-dir phase-1/week-1 --reload

Then open http://localhost:8000/docs — FastAPI builds a live, clickable
API explorer automatically, generated straight from the Pydantic models
in models.py. Nobody hand-writes that page; it can't drift out of sync
with the real code the way a hand-written doc can.
"""

from __future__ import annotations

import logging
import time
from collections.abc import Awaitable, Callable
from uuid import UUID

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from notes_service.models import Note, NoteCreate, NoteList
from notes_service.storage import NoteNotFoundError, NoteStore

# Structured-ish logging: every line has a timestamp and a level, so when
# something breaks at 2am, the log tells you when and how badly, not just
# that something printed.
logger = logging.getLogger("notes")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

app = FastAPI(title="Notes Service", version="0.1.0")

# One shared store for the process. Week 2 replaces this with a real
# database connection — everything that talks to `store` stays unchanged.
store = NoteStore()


@app.middleware("http")
async def log_requests(
    request: Request,
    call_next: Callable[[Request], Awaitable[JSONResponse]],
) -> JSONResponse:
    """Times and logs every single request that hits this service.

    Without this, "the app feels slow" is a guess. With it, you can point
    at the exact endpoint and the exact millisecond count. This is the
    smallest possible version of observability — full tracing comes in
    Phase 6, but the habit starts here.
    """
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "%s %s -> %d (%.1fms)",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


@app.exception_handler(NoteNotFoundError)
async def note_not_found_handler(request: Request, exc: NoteNotFoundError) -> JSONResponse:
    """Turns an internal "not found" into a proper HTTP 404 with a message
    a caller can act on — never a raw Python stack trace. A stack trace
    leaking to a client is both unprofessional and a security leak: it
    tells an attacker your file paths and library versions for free.
    """
    return JSONResponse(status_code=404, content={"detail": str(exc)})


@app.get("/health")
def health() -> dict[str, str]:
    """Infrastructure asks this "are you alive?" question constantly —
    load balancers, deployment tools, monitoring dashboards. It touches no
    business logic on purpose: if THIS breaks, nothing works, full stop.
    """
    return {"status": "ok"}


@app.post("/notes", response_model=Note, status_code=201)
def create_note(payload: NoteCreate) -> Note:
    """Create a note.

    FastAPI validates `payload` against NoteCreate BEFORE this function
    body runs at all. A request missing "title", or with an empty body,
    never reaches this line — it's rejected at the door with a 422 and a
    message stating exactly what was wrong.
    """
    note = Note(title=payload.title, body=payload.body)
    return store.create(note)


@app.get("/notes/{note_id}", response_model=Note)
def get_note(note_id: UUID) -> Note:
    """Fetch one note by id.

    FastAPI rejects a malformed id (not a valid UUID shape) automatically,
    before store.get() is ever called — bad input never reaches storage.
    """
    return store.get(note_id)


@app.get("/notes", response_model=NoteList)
def list_notes(limit: int = 50, offset: int = 0) -> NoteList:
    """List notes, newest first, with pagination.

    Defaults mean calling this with no parameters still works. A caller
    with a huge collection can page through it instead of one request
    trying to return everything at once and timing out.
    """
    items, total = store.list(limit=limit, offset=offset)
    return NoteList(items=items, total=total)
