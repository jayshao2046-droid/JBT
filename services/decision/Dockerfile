# ─── Stage 1: 依赖安装 ───────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /app

COPY pyproject.toml ./
RUN pip install --no-cache-dir --upgrade pip setuptools wheel --timeout=300 && \
    pip install --no-cache-dir poetry==1.8.3 -i https://pypi.tuna.tsinghua.edu.cn/simple --timeout=300 && \
    poetry config virtualenvs.create false && \
    poetry source add --priority=primary tuna https://pypi.tuna.tsinghua.edu.cn/simple && \
    poetry install --only main --no-interaction --no-ansi

# ─── Stage 2: 运行镜像 ───────────────────────────────────────────────────────
FROM python:3.11-slim AS runner

WORKDIR /app

COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

COPY src/ ./src/

RUN mkdir -p /runtime /app/configs

ENV PYTHONPATH=/app
ENV JBT_SERVICE_NAME=decision
ENV JBT_SERVICE_PORT=8104

EXPOSE 8104

HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8104/health')" || exit 1

CMD ["python3", "-m", "uvicorn", "src.api.app:app", "--host", "0.0.0.0", "--port", "8104", "--workers", "2"]
