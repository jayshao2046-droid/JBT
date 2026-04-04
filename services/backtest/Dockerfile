# ────────────────────────────────────────────────
# JBT Backtest API — 生产 Docker 镜像
# 端口: 8103
# 环境变量: 参见 .env.example
# ────────────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# 安装 Python 依赖（固定版本，预编译 wheel 无需 gcc）
RUN pip install --no-cache-dir \
    fastapi==0.128.8 \
    "uvicorn[standard]==0.39.0" \
    tqsdk==3.9.1 \
    pydantic==2.12.5 \
    websockets==15.0.1 \
    python-multipart

# 再复制源码（变更频率高，放后面）
COPY services/backtest/src/ ./services/backtest/src/
COPY shared/ ./shared/

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 8103

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8103/api/v1/health')"

CMD ["python", "-m", "uvicorn", "services.backtest.src.api.app:app", \
     "--host", "0.0.0.0", "--port", "8103", "--log-level", "info"]
