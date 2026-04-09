# syntax=docker/dockerfile:1.7

FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    SMARTSPEND_LOG_DIR=/app/backend/logs

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    gcc \
    g++ \
    libgomp1 \
    tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

COPY backend/requirements.txt /tmp/requirements.txt
RUN pip install --upgrade pip && pip install -r /tmp/requirements.txt

RUN groupadd --system smartspend && useradd --system --gid smartspend --create-home smartspend

COPY backend /app/backend

RUN mkdir -p /app/backend/data /app/backend/logs && chown -R smartspend:smartspend /app

USER smartspend

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=5s --start-period=45s --retries=5 CMD curl --fail http://127.0.0.1:8001/health || exit 1

CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8001"]
