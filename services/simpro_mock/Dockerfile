# Build stage: install the locked dependency set (uv.lock) into /opt/venv.
FROM python:3.12.3-slim-bookworm AS build
COPY --from=ghcr.io/astral-sh/uv:0.12.15 /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PYTHON=/usr/local/bin/python3.12 \
    UV_PROJECT_ENVIRONMENT=/opt/venv
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --locked

# Runtime stage: same base image, no uv, non-root user.
FROM python:3.12.3-slim-bookworm
RUN useradd --system --user-group --uid 10001 --no-create-home \
    --shell /usr/sbin/nologin app
COPY --from=build /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

WORKDIR /app
COPY alembic.ini .
COPY alembic/ alembic/
COPY simpro_mock/ simpro_mock/

USER app
EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && python -m simpro_mock.seed && uvicorn simpro_mock.main:app --host 0.0.0.0 --port 8000"]
