# Notes Service — Weeks 1–2

A small API for creating, fetching, and listing notes. Deliberately simple —
the point isn't to impress, it's to prove real engineering qualities hold
on something small before scaling up.

This also isn't throwaway practice: it's the same shape as the document
storage Phase 3 builds for RAG. Same three moves — save something, fetch it
back, list what you have.

**Week 1** built the API — validation, error handling, tests, logging,
containerization. **Week 2** swapped the storage from an in-memory
dictionary to real Postgres — migrations, an index proven with real
numbers, connection pooling, and a first, isolated look at pgvector.

## Run it

Start the database first (from the repo root):

```bash
docker compose up -d
```

Then:

```bash
uv run uvicorn notes_service.main:app --app-dir phase-1/week-1 --reload
```

Open http://localhost:8000/docs — a live, clickable API explorer, generated
automatically from the Pydantic models. Nobody wrote that page by hand.

## Apply the database schema

```bash
cd phase-1/week-1
uv run alembic upgrade head
```

Applies every migration in order. Safe to re-run — already-applied
migrations are skipped.

## Run the tests

```bash
uv run pytest phase-1/week-1/tests -v
```

13 tests, each proving one promise the service makes — now running against
the real database, not memory.

## Run the week 2 proof scripts

```bash
# proves an index actually made a search faster — real timed numbers
uv run python phase-1/week-1/scripts/benchmark_index.py

# proves text -> embedding -> Postgres -> back out works end to end
uv run python phase-1/week-1/scripts/store_first_vector.py
```

## Run it in a container (from the repo root, not this folder)

```bash
docker build -f phase-1/week-1/Dockerfile -t notes-service .
docker run -p 8000:8000 notes-service
```

## Measured: does the index actually help?

Ran on 20,000 seeded rows, searching for one exact title. `EXPLAIN ANALYZE`
reports Postgres's real execution time, not wall-clock (which includes
Python/network overhead on top):

| | Before index | After index |
|---|---|---|
| Plan | `Seq Scan` — checked all 20,000 rows | `Bitmap Index Scan` — went straight there |
| Execution time | 1.756ms | 0.145ms |
| Rows removed by filter | 20,000 | — |

At 20k rows the gap is milliseconds. The mechanism is what matters — at
20 million rows this is the difference between instant and unusable.

## The six qualities, and where each one lives

| # | Quality | Where |
|---|---|---|
| 1 | Doesn't trust input | `models.py` — Pydantic rejects bad data before business logic runs |
| 2 | Survives being wrong | `main.py` — `NoteNotFoundError` becomes a clean 404, never a stack trace |
| 3 | Provably works | `tests/test_api.py` — 13 tests, run in under a second |
| 4 | Measured | `main.py` — every request logs its path, status, and duration |
| 5 | Runs anywhere | `Dockerfile` — same container runs on any machine with Docker |
| 6 | Debuggable at 2am | The logging middleware — every request leaves a trace |

## Endpoints

| Method | Path | Does |
|---|---|---|
| `GET` | `/health` | Are you alive? No business logic touched. |
| `POST` | `/notes` | Create a note. `title` + `body`, both required, non-empty. |
| `GET` | `/notes/{id}` | Fetch one note. 404 if it doesn't exist. |
| `GET` | `/notes?limit=&offset=` | List notes, newest first, paginated. |

## Files added in week 2

| File | Job |
|---|---|
| `notes_service/db.py` | Connects to Postgres, configures the connection pool |
| `notes_service/db_models.py` | The real database schema, as Python |
| `notes_service/storage.py` | Rewritten to use real Postgres — same public interface as week 1 |
| `migrations/versions/*_create_notes_table.py` | Migration 1: creates the table |
| `migrations/versions/*_add_index_on_notes_title.py` | Migration 2: adds the index |
| `scripts/benchmark_index.py` | Seeds 20k rows, measures before/after the index |
| `scripts/store_first_vector.py` | Text → embedding → Postgres → back out |

## What's deliberately missing (and why)

- **No authentication.** Anyone can call any endpoint. Not a real-world
  gap yet — that's a later, separate lesson.
- **No real search.** The vector script stores one embedding in an
  isolated table to prove the mechanism. Actual "find notes by meaning"
  search is Phase 3.
- **No AI in the API itself.** On purpose. This is the plain engineering
  foundation everything in Phase 2 onward gets built on top of.
