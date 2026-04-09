# ─── Stage 1: 依赖安装 ───────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

COPY requirements.txt .
# openctp-ctp 仅有 amd64 wheel；arm64 环境跳过，运行时走 stub 模式
RUN pip install --no-cache-dir --upgrade pip \
    && grep -v '^openctp-ctp' requirements.txt | pip install --no-cache-dir -r /dev/stdin \
    && pip install --no-cache-dir openctp-ctp 2>/dev/null || echo "openctp-ctp not available on this platform, using stub mode"

# ─── Stage 2: 运行镜像 ───────────────────────────────────────────────────────
FROM python:3.11-slim AS runner

WORKDIR /app

# CTP SDK .so 加载时需要 en_US.UTF-8 locale；locales-all 预编译全量 locale 数据，避免 glibc locale-archive 兼容问题
RUN apt-get update && apt-get install -y --no-install-recommends locales-all \
    && rm -rf /var/lib/apt/lists/*
ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY src/ ./src/
COPY configs/ ./configs/

RUN mkdir -p /runtime

ENV PYTHONPATH=/app
ENV JBT_SERVICE_NAME=sim-trading
ENV JBT_SERVICE_PORT=8101

EXPOSE 8101

HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8101/health')" || exit 1

CMD ["python3", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8101"]
