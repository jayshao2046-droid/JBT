FROM python:3.11-slim-bookworm

LABEL service="jbt-data"
LABEL version="1.0.0"

WORKDIR /app

# Use China mirror for apt (speeds up build on Mini)
RUN sed -i 's|deb.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list.d/debian.sources 2>/dev/null || \
    sed -i 's|deb.debian.org|mirrors.aliyun.com|g' /etc/apt/sources.list 2>/dev/null || true

# Install system deps (curl for healthcheck, tzdata for timezone) via apt, supervisor via pip
RUN apt-get update -o Acquire::Retries=3 && \
    apt-get install -y --no-install-recommends curl tzdata && \
    rm -rf /var/lib/apt/lists/* || \
    echo "apt-get failed, skipping curl"

# Set timezone
ENV TZ=Asia/Shanghai
RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Python deps + supervisor via pip
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip install --no-cache-dir supervisor -i https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip install --no-cache-dir -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple

# Application code
COPY src/ ./src/
COPY tests/ ./tests/
COPY configs/ ./configs/

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
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8105/health')" || exit 1

CMD ["supervisord", "-n", "-c", "/etc/supervisor/conf.d/jbt-data.conf"]
