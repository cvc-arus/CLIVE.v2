FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY alembic.ini .
COPY alembic/ alembic/
COPY simpro_mock/ simpro_mock/

EXPOSE 8000

CMD ["sh", "-c", "alembic upgrade head && python -m simpro_mock.seed && uvicorn simpro_mock.main:app --host 0.0.0.0 --port 8000"]