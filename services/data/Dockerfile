FROM python:3.11-slim

LABEL service="jbt-data"
LABEL version="0.2.0"

WORKDIR /app

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl rsync && \
    rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Application code
COPY src/ ./services/data/src/
COPY tests/ ./services/data/tests/
COPY configs/ ./services/data/configs/

# Shared contracts (if needed at runtime)
# COPY ../../shared/contracts/ ./shared/contracts/

# Runtime dirs
RUN mkdir -p /runtime/data /runtime/cache /runtime/logs /runtime/backup

ENV PYTHONPATH=/app
ENV JBT_SERVICE_NAME=data
ENV JBT_SERVICE_PORT=8105

EXPOSE 8105

HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
    CMD curl -f http://localhost:8105/health || exit 1

CMD ["python", "-m", "uvicorn", "services.data.src.main:app", "--host", "0.0.0.0", "--port", "8105"]
