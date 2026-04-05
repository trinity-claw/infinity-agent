# =============================================================================
# Infinity Agent — Multi-stage Docker Build
# =============================================================================
# =============================================================================
# Stage 1: Build React Frontend
# =============================================================================
FROM node:20-slim AS frontend-builder
WORKDIR /app
COPY frontend-react/package*.json ./
RUN npm ci
COPY frontend-react/ ./
RUN npm run build

# =============================================================================
# Stage 2: Build Python Dependencies
# =============================================================================
FROM python:3.12-slim AS builder

WORKDIR /app

# Install uv for fast dependency resolution
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Copy dependency files
COPY pyproject.toml .

# Install dependencies
RUN uv pip install --system --no-cache .

# =============================================================================
FROM python:3.12-slim AS runtime

WORKDIR /app

# Create non-root user
RUN adduser --disabled-password --gecos "" appuser

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy application code
COPY src/ ./src/
COPY --from=frontend-builder /app/dist ./frontend-react/dist
COPY scripts/ ./scripts/
COPY pyproject.toml .

# Create data directory for ChromaDB
RUN mkdir -p /app/data/chroma_db && chown -R appuser:appuser /app

USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python -c "import httpx; httpx.get('http://localhost:8000/v1/health')" || exit 1

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
