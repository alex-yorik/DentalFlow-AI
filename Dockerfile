FROM python:3.12-slim AS builder

WORKDIR /app

COPY requirements-prod.txt requirements.txt
RUN python -m venv /opt/venv && \
    /opt/venv/bin/pip install --no-cache-dir -r requirements.txt && \
    rm -rf /opt/venv/share /opt/venv/include

FROM python:3.12-slim AS runtime

RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid appgroup --no-create-home appuser && \
    mkdir -p /app/data && \
    chown appuser:appgroup /app/data

WORKDIR /app

COPY --from=builder /opt/venv /opt/venv
ENV PATH=/opt/venv/bin:$PATH

COPY . .

USER appuser

ARG HEALTHCHECK_INTERVAL=30s
ARG HEALTHCHECK_TIMEOUT=10s
ARG HEALTHCHECK_START_PERIOD=10s
ARG HEALTHCHECK_RETRIES=3

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD python docker/healthcheck.py

CMD ["python", "-m", "src.main"]