"""Health check for the course environment.

Run it any time something feels broken:

    uv run python check_setup.py

It checks each piece in order and tells you exactly what to fix if one
of them fails. Nothing here is clever — it's a smoke alarm.
"""

from __future__ import annotations

import os
import sys

from dotenv import load_dotenv

# Reads the .env file and puts those values into the environment, so the
# rest of the code can read them without them being written in the code.
load_dotenv()

PASS = "  [ok]   "
FAIL = "  [FAIL] "
SKIP = "  [skip] "

failures: list[str] = []


def report(ok: bool, label: str, detail: str = "", fix: str = "") -> bool:
    """Print one result line. Record the fix instruction if it failed."""
    mark = PASS if ok else FAIL
    print(f"{mark}{label}" + (f" — {detail}" if detail else ""))
    if not ok and fix:
        failures.append(f"{label}: {fix}")
    return ok


def check_env_file() -> bool:
    """Is there a .env file with the settings we expect?"""
    print("\n1. Settings file")
    if not os.path.exists(".env"):
        return report(
            False,
            ".env exists",
            "not found",
            "Run: copy .env.example .env",
        )
    report(True, ".env exists")

    ok = True
    for name in ("OLLAMA_BASE_URL", "LOCAL_CHAT_MODEL", "DATABASE_URL"):
        value = os.getenv(name, "")
        ok &= report(
            bool(value),
            name,
            value if value else "missing",
            f"Open .env and set {name}.",
        )
    return ok


def check_local_chat() -> bool:
    """Can we get an answer out of the local model on the GPU?"""
    print("\n2. Local chat model")
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
    model = os.getenv("LOCAL_CHAT_MODEL", "qwen3:8b")

    try:
        from openai import OpenAI
    except ImportError:
        return report(False, "openai library", "missing", "Run: uv sync")

    # Ollama speaks the same protocol as OpenAI, so the same client works.
    # Only the address changes. This is why one codebase can target both.
    client = OpenAI(base_url=base_url, api_key=os.getenv("OLLAMA_API_KEY", "ollama"))

    try:
        models = [m.id for m in client.models.list().data]
    except Exception as exc:  # noqa: BLE001 — we want the message, whatever it is
        return report(
            False,
            "Ollama reachable",
            type(exc).__name__,
            "Start Ollama (it runs in the system tray), then retry. "
            f"Error was: {exc}",
        )

    report(True, "Ollama reachable", f"{len(models)} model(s) downloaded")

    if model not in models:
        return report(
            False,
            f"model '{model}'",
            "not downloaded",
            f"Run: ollama pull {model}",
        )

    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": "Reply with the single word: ready"}],
            # Generous on purpose. "Thinking" models reason to themselves before
            # answering, and that reasoning spends tokens from this same budget.
            # Set this too low and you get an empty reply with no error at all.
            max_tokens=512,
        )
        choice = resp.choices[0]
        text = (choice.message.content or "").strip()

        # finish_reason tells you WHY it stopped:
        #   "stop"   = the model finished its answer
        #   "length" = you cut it off — the answer is incomplete
        # Never trust a response without checking this.
        if choice.finish_reason == "length":
            return report(
                False,
                "live call",
                "hit the token limit before finishing",
                "Raise max_tokens — the model ran out of room mid-answer.",
            )

        used = resp.usage.completion_tokens if resp.usage else "?"
        return report(True, "live call", f'replied "{text[:40]}" using {used} tokens')
    except Exception as exc:  # noqa: BLE001
        return report(False, "live call", type(exc).__name__, f"Error was: {exc}")


def check_local_embeddings() -> bool:
    """Can we turn text into numbers locally? Needed from week 7."""
    print("\n3. Local embedding model")
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434/v1")
    model = os.getenv("LOCAL_EMBED_MODEL", "nomic-embed-text")

    try:
        from openai import OpenAI

        client = OpenAI(base_url=base_url, api_key=os.getenv("OLLAMA_API_KEY", "ollama"))
        resp = client.embeddings.create(model=model, input="hello")
        dims = len(resp.data[0].embedding)
        return report(True, "embedding call", f"got a {dims}-number vector back")
    except Exception as exc:  # noqa: BLE001
        return report(
            False,
            "embedding call",
            type(exc).__name__,
            f"Run: ollama pull {model}",
        )


def check_cloud_keys() -> bool:
    """Optional. Not needed until Phase 5."""
    print("\n4. Cloud providers (optional)")
    for name in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY"):
        value = os.getenv(name, "")
        if value:
            report(True, name, "set")
        else:
            print(f"{SKIP}{name} — not set (fine, not needed yet)")
    return True


def check_database() -> bool:
    """Is the database container up, and does it have the vector add-on?"""
    print("\n5. Database")
    url = os.getenv("DATABASE_URL", "")
    if not url:
        return report(False, "DATABASE_URL", "not set", "Set it in .env.")

    try:
        import psycopg
    except ImportError:
        return report(False, "psycopg installed", "missing", "Run: uv sync")

    try:
        with psycopg.connect(url, connect_timeout=5) as conn, conn.cursor() as cur:
            cur.execute("SELECT version();")
            row = cur.fetchone()
            version = row[0].split(",")[0] if row else "unknown"
            report(True, "connection", version)

            # Turn on pgvector. Safe to run repeatedly.
            cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            conn.commit()

            # Prove it works by doing an actual distance calculation.
            cur.execute("SELECT '[1,2,3]'::vector <-> '[1,2,4]'::vector;")
            row = cur.fetchone()
            distance = row[0] if row else None
            return report(
                distance is not None,
                "pgvector",
                f"distance test returned {distance}",
            )
    except Exception as exc:  # noqa: BLE001
        return report(
            False,
            "connection",
            type(exc).__name__,
            f"Start Docker Desktop, then run: docker compose up -d. Error was: {exc}",
        )


def main() -> int:
    print("=" * 60)
    print("  Course environment check")
    print("=" * 60)

    check_env_file()
    check_local_chat()
    check_local_embeddings()
    check_cloud_keys()
    check_database()

    print("\n" + "=" * 60)
    if failures:
        print(f"  {len(failures)} thing(s) to fix:\n")
        for item in failures:
            print(f"  - {item}")
        print("=" * 60)
        return 1

    print("  Everything works. You're ready for Phase 1.")
    print("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
