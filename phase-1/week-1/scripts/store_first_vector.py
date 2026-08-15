"""First contact with pgvector.

Turn a sentence into numbers using the local embedding model, save those
numbers next to some text in Postgres, read them back. Not search yet —
Phase 3 builds that on top of this. This just proves the plumbing works:
model -> Postgres column -> round trip.

Run it:
    uv run python phase-1/week-1/scripts/store_first_vector.py
"""

from __future__ import annotations

import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv  # noqa: E402
from notes_service.db import engine  # noqa: E402
from openai import OpenAI  # noqa: E402
from sqlalchemy import text  # noqa: E402

load_dotenv()

EMBED_MODEL = "nomic-embed-text"


def main() -> None:
    # Ollama speaks the OpenAI protocol, so the OpenAI library works
    # against it unchanged — only the address is different.
    client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

    note_text = "Buy milk, eggs, and bread for the week."
    print(f"embedding: {note_text!r}")

    response = client.embeddings.create(model=EMBED_MODEL, input=note_text)
    vector = response.data[0].embedding
    print(f"got {len(vector)} numbers back — that's the meaning, as coordinates")

    # A separate, throwaway table — deliberately not the real `notes`
    # table. Phase 3 is where embeddings join the real schema properly;
    # this is just proving the mechanism works in isolation first.
    with engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        conn.execute(
            text(
                """
                CREATE TABLE IF NOT EXISTS note_embeddings (
                    id UUID PRIMARY KEY,
                    note_text TEXT NOT NULL,
                    embedding vector(768) NOT NULL
                )
                """
            )
        )
        conn.execute(
            text(
                """
                INSERT INTO note_embeddings (id, note_text, embedding)
                VALUES (:id, :note_text, :embedding)
                """
            ),
            {"id": str(uuid.uuid4()), "note_text": note_text, "embedding": str(vector)},
        )

    with engine.connect() as conn:
        row = conn.execute(
            text("SELECT note_text, embedding FROM note_embeddings LIMIT 1")
        ).fetchone()
        assert row is not None
        print("\nread back from Postgres:")
        print(f"  text stored: {row[0]}")
        print(f"  first few of {len(vector)} numbers: {str(row[1])[:90]}...")


if __name__ == "__main__":
    main()
