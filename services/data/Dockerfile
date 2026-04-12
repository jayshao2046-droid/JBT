FROM python:3.11-slim

LABEL service="jbt-data"
LABEL version="1.0.0"

WORKDIR /app

# System deps + supervisor
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl rsync supervisor && \
    rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# Application code
COPY src/ ./services/data/src/
COPY tests/ ./services/data/tests/
COPY configs/ ./services/data/configs/

# Supervisord config
COPY supervisord.conf /etc/supervisor/conf.d/jbt-data.conf

# Data directories (will be mounted as volume in production)
RUN mkdir -p /data/parquet /data/logs /data/cache /data/backup \
             /var/log/supervisor

ENV PYTHONPATH=/app
ENV JBT_SERVICE_NAME=jbt-data
ENV JBT_SERVICE_PORT=8105
ENV DATA_STORAGE_ROOT=/data
ENV JBT_DATA_LOG_DIR=/data/logs

EXPOSE 8105

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8105/health || exit 1

CMD ["supervisord", "-n", "-c", "/etc/supervisor/conf.d/jbt-data.conf"]
