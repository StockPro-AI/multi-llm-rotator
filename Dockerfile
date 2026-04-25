# syntax=docker/dockerfile:1
# ============================================================
# multi-llm-rotator — Production Dockerfile
# ============================================================
FROM python:3.12-slim

# Metadata
LABEL org.opencontainers.image.title="multi-llm-rotator"
LABEL org.opencontainers.image.description="Universal multi-account LLM rotation for Gemini, Claude & ChatGPT"
LABEL org.opencontainers.image.source="https://github.com/StockPro-AI/multi-llm-rotator"

# System packages (minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash rotator
WORKDIR /app

# Install Python dependencies first (layer cache)
COPY requirements.txt pyproject.toml ./
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy the package source
COPY multi_llm_rotator/ ./multi_llm_rotator/
COPY examples/ ./examples/

# Install the package itself (editable so examples work)
RUN pip install --no-cache-dir -e .

# Switch to non-root user
USER rotator

# Health check — just verifies the module is importable
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD python -c "import multi_llm_rotator; print('ok')" || exit 1

# Default command: show CLI help
CMD ["python", "-m", "multi_llm_rotator", "--help"]
