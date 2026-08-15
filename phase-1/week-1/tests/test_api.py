"""Tests for the Notes service.

Each test proves exactly one promise the service makes. Run all of them:

    uv run pytest

Read these even if you don't write tests like this yet — the names alone
tell the story of what "correct" means for this service. That's the real
value of good test names: they're documentation nobody has to maintain
separately, because they're checked by running them.
"""

from __future__ import annotations

from fastapi.testclient import TestClient
from notes_service.db import SessionLocal
from notes_service.db_models import NoteRow
from notes_service.main import app
from sqlalchemy import delete

client = TestClient(app)


def setup_function() -> None:
    """Reset the notes table before every test.

    This used to be `store._notes.clear()` against a Python dict. It's
    now a real DELETE against Postgres — but notice not one test body
    below changed. They only ever talked to the HTTP API, never to
    storage internals, so swapping what's behind the API broke nothing.
    That isolation is the actual payoff of testing through the API layer.
    """
    with SessionLocal() as session:
        session.execute(delete(NoteRow))
        session.commit()


# --- The service is alive ---------------------------------------------


def test_health_check() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


# --- Creating a note ----------------------------------------------------


def test_create_note_returns_201_and_the_note() -> None:
    response = client.post("/notes", json={"title": "Groceries", "body": "Milk, eggs"})
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Groceries"
    assert data["body"] == "Milk, eggs"
    assert "id" in data
    assert "created_at" in data


def test_create_note_rejects_empty_title() -> None:
    """An empty title should never reach storage — Pydantic blocks it
    before create_note() runs at all."""
    response = client.post("/notes", json={"title": "", "body": "something"})
    assert response.status_code == 422


def test_create_note_rejects_whitespace_only_title() -> None:
    """ "   " looks non-empty by character count but means nothing. The
    custom validator in models.py catches what a plain length check
    would miss."""
    response = client.post("/notes", json={"title": "   ", "body": "something"})
    assert response.status_code == 422


def test_create_note_rejects_missing_body() -> None:
    response = client.post("/notes", json={"title": "No body"})
    assert response.status_code == 422


def test_create_note_ignores_a_client_supplied_id() -> None:
    """A caller cannot choose their own id — NoteCreate has no id field.
    Even if one is smuggled into the request body, it's silently ignored,
    not honored."""
    response = client.post(
        "/notes",
        json={"title": "Sneaky", "body": "x", "id": "11111111-1111-1111-1111-111111111111"},
    )
    assert response.status_code == 201
    assert response.json()["id"] != "11111111-1111-1111-1111-111111111111"


# --- Fetching a note ------------------------------------------------------


def test_get_note_returns_the_note_that_was_created() -> None:
    created = client.post("/notes", json={"title": "Find me", "body": "here"}).json()
    response = client.get(f"/notes/{created['id']}")
    assert response.status_code == 200
    assert response.json()["title"] == "Find me"


def test_get_note_with_unknown_id_returns_404_not_a_crash() -> None:
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = client.get(f"/notes/{fake_id}")
    assert response.status_code == 404
    assert "detail" in response.json()


def test_get_note_with_malformed_id_returns_422_not_a_500() -> None:
    """ "not-a-uuid" isn't a valid id shape at all. FastAPI rejects it
    before it ever reaches the storage layer — the difference between a
    handled bad-input case (422) and an unhandled server crash (500)."""
    response = client.get("/notes/not-a-uuid")
    assert response.status_code == 422


# --- Listing notes ---------------------------------------------------------


def test_list_notes_returns_everything_created() -> None:
    client.post("/notes", json={"title": "One", "body": "a"})
    client.post("/notes", json={"title": "Two", "body": "b"})
    response = client.get("/notes")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2


def test_list_notes_respects_limit() -> None:
    for i in range(5):
        client.post("/notes", json={"title": f"Note {i}", "body": "x"})
    response = client.get("/notes?limit=2")
    data = response.json()
    assert data["total"] == 5  # total still reflects everything that exists
    assert len(data["items"]) == 2  # but only a page came back


def test_list_notes_newest_first() -> None:
    first = client.post("/notes", json={"title": "First", "body": "x"}).json()
    second = client.post("/notes", json={"title": "Second", "body": "x"}).json()
    items = client.get("/notes").json()["items"]
    assert items[0]["id"] == second["id"]
    assert items[1]["id"] == first["id"]


def test_list_notes_on_empty_store_returns_empty_not_an_error() -> None:
    response = client.get("/notes")
    assert response.status_code == 200
    assert response.json() == {"items": [], "total": 0}
