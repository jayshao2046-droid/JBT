# ─── Stage 1: 依赖安装 ────────────────────────────────────────────────────────
FROM swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/library/python:3.11-slim AS builder

WORKDIR /app

# 安装系统依赖（tqsdk 编译时需要）
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc g++ libffi-dev libssl-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ─── Stage 2: 运行镜像 ───────────────────────────────────────────────────────
FROM swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/library/python:3.11-slim AS runner

WORKDIR /app

# 从 builder 复制依赖
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# 复制源码
COPY src/ ./src/
COPY configs/ ./configs/

# 运行时目录由 docker-compose 挂载卷创建，此处仅预建空目录作为 fallback
RUN mkdir -p /runtime/strategies /runtime/results /runtime/backtests /runtime/reports

ENV PYTHONPATH=/app
ENV JBT_SERVICE_NAME=backtest
ENV JBT_SERVICE_PORT=8103

EXPOSE 8103

HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8103/api/health')" || exit 1

CMD ["python3", "-m", "uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8103"]
