# SkillGap Backend Dockerfile
# Optimized for free cloud hosting (Render 512MB RAM, Hugging Face Spaces, Railway)
FROM python:3.12-slim

# Prevent Python bytecode, force unbuffered logs, and constrain thread counts to stay under 512MB RAM
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    USE_SLM=false \
    PORT=8000 \
    OMP_NUM_THREADS=1 \
    MKL_NUM_THREADS=1 \
    OPENBLAS_NUM_THREADS=1 \
    NUMEXPR_NUM_THREADS=1 \
    TOKENIZERS_PARALLELISM=false

WORKDIR /app

# Install minimal OS dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install lightweight CPU-only PyTorch FIRST so pip does NOT download 3+ GB of CUDA / NVIDIA packages
RUN pip install --no-cache-dir torch --index-url https://download.pytorch.org/whl/cpu

# Copy requirements and install remaining dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download and cache NLP models at build time
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

# Run uvicorn server with dynamic port support (Render passes $PORT, default 8000)
CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
