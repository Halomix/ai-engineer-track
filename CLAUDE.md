# Project notes for AI assistants

This file is read automatically by Claude Code every session. It is how the
assistant learns the house rules without me repeating them. Keep it short and
factual — it is loaded into every conversation, so waffle costs money.

## What this is

A 26-week learning repo for the AI Engineer (LLM/RAG) track. Each phase gets
its own folder. Code here is written to be *understood*, not just to work.

## Ground rules

- **I write the code through Phase 2. You review it.** Do not hand me finished
  implementations during the foundations phases — point at the problem and let
  me fix it. From Phase 3 you can write more, but explain anything non-obvious.
- Explain new concepts in plain language first, then show the code.
- Prefer boring, readable solutions over clever ones.
- If a change touches more than three files, describe the plan before editing.

## Models

This course runs on **local models via Ollama** by default, on an RTX 3050
(6 GB VRAM). Cloud APIs are optional and unused until Phase 5.

- Chat: `qwen3:8b` — fits in 6 GB, good instruction following
- Embeddings: `nomic-embed-text` — small and fast
- Ollama exposes an OpenAI-compatible endpoint at `http://localhost:11434/v1`,
  so the `openai` library works against it unchanged. Only the base URL differs.
  Keep code provider-agnostic so swapping to a cloud model is a config change.

When suggesting models, respect the 6 GB VRAM ceiling. Anything above ~8B
parameters at 4-bit will spill into system RAM and crawl.

## Commands

```
uv sync                      # install/update dependencies
uv run python check_setup.py # verify the whole environment works
uv run ruff check .          # find style problems and likely bugs
uv run ruff format .         # auto-format the code
uv run mypy .                # check types
uv run pytest                # run tests
docker compose up -d         # start the local database
docker compose down          # stop it
ollama list                  # show downloaded models
ollama pull <model>          # download a model
ollama ps                    # show what's loaded in VRAM right now
```

## Layout

```
.env             real secrets — NEVER commit, never print, never paste
.env.example     template showing which keys exist (safe to commit)
check_setup.py   environment health check
docker-compose.yml  local Postgres with the pgvector add-on
phase-1/ ...     one folder per phase
```

## Hard rules

- Never print, log, or echo the contents of `.env` or any API key.
- Never commit `.env`. If it ever gets staged, stop and tell me.
- Every project that calls a model must log three numbers per request:
  latency, tokens, and cost. This is not optional — it is the whole point.
