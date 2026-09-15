FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY pyproject.toml uv.lock ./
ENV UV_HTTP_TIMEOUT=120
ENV UV_LOCK_TIMEOUT=600
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --frozen --no-install-project

COPY app ./app

EXPOSE 8000

CMD ["uv", "run", "python", "app/server.py"]