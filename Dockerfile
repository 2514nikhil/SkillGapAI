# SkillGap Backend Dockerfile
# Optimized for Hugging Face Spaces, Render, and Linux VPS deployment.
FROM python:3.12-slim

# Prevent Python from writing .pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    USE_SLM=false \
    PORT=8000

WORKDIR /app

# Install system dependencies needed for compiling native extensions and parsing
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download and cache NLP models at build time so runtime has zero latency
RUN python -m spacy download en_core_web_sm
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')"

# Copy application source code and precomputed data artifacts
COPY config.py .
COPY api/ ./api/
COPY ml/ ./ml/
COPY data/processed/ ./data/processed/

# Create a non-privileged user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

# Run uvicorn server with dynamic port support (compatible with Render / Hugging Face Spaces)
CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
