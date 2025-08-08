# Stage 1: Build
FROM python:3.11-slim AS builder
WORKDIR /workspace
# mount cache for pip to speed up builds
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip && \
    pip install agentbeats

# Stage 2: Runtime
FROM python:3.11-slim AS runtime
WORKDIR /workspace
RUN apt-get update && \
    apt-get install -y --no-install-recommends bash curl dos2unix ca-certificates && \
    rm -rf /var/lib/apt/lists/*

RUN apt-get update && apt-get install -y --no-install-recommends socat && \
    rm -rf /var/lib/apt/lists/*

# copy python from builder stage
COPY --from=builder /usr/local /usr/local

# change CRLF to LF
COPY entrypoint.sh /workspace/entrypoint.sh
RUN dos2unix /workspace/entrypoint.sh && chmod +x /workspace/entrypoint.sh

ENV SCENARIO_ROOT=/workspace \
    PYTHONUNBUFFERED=1 

# TODO: not considering health check now
# HEALTHCHECK --interval=30s  \
#             --timeout=5s \
#             --retries=5 \
#             CMD curl -fs "http://localhost:${HEALTHCHECK_PORT:-9010}/health" || exit 1

ENTRYPOINT ["/workspace/entrypoint.sh"]
