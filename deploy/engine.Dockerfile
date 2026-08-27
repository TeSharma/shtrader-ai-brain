# Shtrader LA engine — public API container.
#
# The deterministic engine works with NO GGUF model: it runs offline with the
# StubProvider, so this image is small and deployable on any container host
# (Render, Railway, Fly.io, GCP, a VPS, ...). The large local Llama model stays
# on the developer's machine.
#
# Build (Dockerfile lives here but the build context is the repo root):
#   docker build -f deploy/engine.Dockerfile -t shtrader-la-engine .
# Run:
#   docker run --rm -p 8000:8000 shtrader-la-engine

FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=8000

WORKDIR /app

# Install runtime deps first for better layer caching.
COPY requirements.txt .
RUN python -m pip install --no-cache-dir -r requirements.txt

# Copy the engine package (the node_modules, .venv and static build are irrelevant
# to the API and are excluded by .dockerignore).
COPY shtrader_la ./shtrader_la

EXPOSE 8000

# Allow any origin for the deployed API (overridable via SHTRADER_API_ALLOWED_ORIGINS).
ENV SHTRADER_API_ALLOWED_ORIGINS="*"

CMD ["python", "-m", "uvicorn", "shtrader_la.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
