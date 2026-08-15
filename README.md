# AI Engineer Track

A 26-week build log working toward the AI Engineer (LLM/RAG) role. Every phase
ends in something that runs and something that was measured.

Models run **locally on the GPU** via Ollama — no API keys, no per-request cost.
Cloud providers are optional and not needed until Phase 5.

## Getting started from a fresh clone

```bash
# 1. Install dependencies (creates a .venv folder automatically)
uv sync

# 2. Create your settings file
copy .env.example .env

# 3. Download the models (one time, a few GB)
ollama pull qwen3:8b
ollama pull nomic-embed-text

# 4. Start the local database (Docker Desktop must be running)
docker compose up -d

# 5. Confirm everything works
uv run python check_setup.py
```

If step 5 prints `Everything works`, you're set.

## Everyday commands

| Command | What it does |
|---|---|
| `uv run python check_setup.py` | Health check — run this first when anything breaks |
| `ollama list` | Show downloaded models |
| `ollama ps` | Show what's currently loaded in GPU memory |
| `docker compose up -d` | Start the database |
| `docker compose down` | Stop the database |
| `uv run ruff check .` | Find style problems and likely bugs |
| `uv run ruff format .` | Auto-format the code |
| `uv run mypy .` | Check types |
| `uv run pytest` | Run tests |

## Hardware

Built and tested on an RTX 3050 with 6 GB of video memory. Models up to
roughly 8 billion parameters fit; larger ones spill into system memory and
become very slow.

## Progress

- [x] **Phase 0** — Environment set up and verified
- [ ] **Phase 1** — Engineering foundations (weeks 1–3)
- [ ] **Phase 2** — LLM API fundamentals (weeks 4–6)
- [ ] **Phase 3** — Retrieval / RAG (weeks 7–11)
- [ ] **Phase 4** — Evaluation (weeks 12–14)
- [ ] **Phase 5** — Agents and MCP (weeks 15–19)
- [ ] **Phase 6** — Production (weeks 20–23)
- [ ] **Phase 7** — Portfolio and applications (weeks 24–26)
