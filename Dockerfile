# ---------- Build stage: install dependencies with uv ----------
FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim AS builder

ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never
WORKDIR /app

COPY pyproject.toml uv.lock .python-version ./
RUN uv sync --frozen --no-dev --no-install-project


# ---------- Runtime stage ----------
FROM python:3.13-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PATH="/app/.venv/bin:$PATH" \
    SQLITE_PATH=/app/data/housing.sqlite3 \
    TZ=Europe/Paris

WORKDIR /app
COPY --from=builder /app/.venv /app/.venv
COPY src ./src

VOLUME ["/app/data"]

CMD ["python", "-m", "src.app"]
