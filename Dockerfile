# syntax=docker/dockerfile:1.17.1
# check=skip=all

ARG PYTHON_VERSION=3.13.6

FROM python:${PYTHON_VERSION}-slim-bookworm as builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN uv sync --frozen

COPY main.py .

FROM python:${PYTHON_VERSION}-slim-bookworm as runner

ENV PATH="/app/.venv/bin:$PATH"

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv
COPY --from=builder /app/main.py /app/main.py

RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app

USER appuser

CMD ["python", "main.py"]
