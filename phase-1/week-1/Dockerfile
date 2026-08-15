# Packages the Notes service so it runs the same way on your laptop,
# a teammate's laptop, or a real server — that's quality #5 from the
# course notes: "someone else can run it."
#
# Build from the REPO ROOT (not this folder), because it needs
# pyproject.toml and uv.lock, which live there:
#
#     docker build -f phase-1/week-1/Dockerfile -t notes-service .
#     docker run -p 8000:8000 notes-service
#
# Then open http://localhost:8000/docs

FROM python:3.12-slim

WORKDIR /app

# Bring in uv itself — much faster than plain pip for installing deps.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy ONLY the dependency files first. Docker caches each step; as long
# as these two files don't change, re-building after an app-code edit
# skips re-downloading every dependency — seconds instead of minutes.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Now copy the actual application code.
COPY phase-1/week-1/notes_service ./notes_service

# Never run a container as root. If something inside ever gets
# compromised, a limited user account is a much smaller problem than
# root access to the whole container.
RUN useradd --create-home appuser
USER appuser

EXPOSE 8000

CMD ["uv", "run", "uvicorn", "notes_service.main:app", "--host", "0.0.0.0", "--port", "8000"]
