FROM python:3.11-slim

WORKDIR /app

RUN pip install --no-cache-dir fastapi uvicorn[standard] pydantic-settings httpx

COPY src/ ./src/
COPY configs/ ./configs/

RUN mkdir -p /runtime

ENV PYTHONPATH=/app
ENV JBT_SERVICE_NAME=dashboard
ENV JBT_SERVICE_PORT=8106

EXPOSE 8106

HEALTHCHECK --interval=15s --timeout=5s --start-period=20s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8106/health')" || exit 1

CMD ["python3", "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8106"]
