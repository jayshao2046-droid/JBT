# --- Stage 1: dependencies -------------------------------------------------
FROM python:3.11-slim AS builder

ARG PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple
ARG PIP_DEFAULT_TIMEOUT=120

WORKDIR /app

COPY requirements.txt .
RUN pip install --disable-pip-version-check --no-cache-dir --upgrade pip \
    && grep -v "^openctp-ctp" requirements.txt > /tmp/requirements-core.txt \
    && pip install --disable-pip-version-check --no-cache-dir --default-timeout ${PIP_DEFAULT_TIMEOUT} -i ${PIP_INDEX_URL} --trusted-host mirrors.aliyun.com -r /tmp/requirements-core.txt \
    && (pip install --disable-pip-version-check --no-cache-dir --default-timeout ${PIP_DEFAULT_TIMEOUT} -i ${PIP_INDEX_URL} --trusted-host mirrors.aliyun.com openctp-ctp || echo "openctp-ctp not available on this platform, using stub mode")

# --- Stage 2: runtime ------------------------------------------------------
FROM python:3.11-slim AS runner

WORKDIR /app

# CTP SDK .so needs locale; LANG=C is glibc built-in, no extra packages needed
RUN sed -i "s|deb.debian.org|mirrors.aliyun.com|g" /etc/apt/sources.list.d/debian.sources 2>/dev/null; \
    sed -i "s|deb.debian.org|mirrors.aliyun.com|g" /etc/apt/sources.list 2>/dev/null; \
    apt-get update && apt-get install -y --no-install-recommends locales-all \
    && rm -rf /var/lib/apt/lists/*
ENV LANG=C
ENV LC_ALL=C

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
