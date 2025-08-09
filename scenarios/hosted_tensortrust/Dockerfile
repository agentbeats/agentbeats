# Stage 1: Build
FROM python:3.11-slim AS builder
WORKDIR /workspace
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --upgrade pip && \
    pip install agentbeats

# Stage 2: Runtime
FROM python:3.11-slim
# TODO: replace with actual repo URL
LABEL org.opencontainers.image.source="TODO: https://github.com/yourrepo" 
WORKDIR /workspace
# copy build artifacts to runtime image, avoiding unnecessary re-installation
COPY --from=builder /usr/local /usr/local
COPY . /workspace

ENV SCENARIO_ROOT=/workspace \
    PYTHONUNBUFFERED=1 \
    AB_HOST=0.0.0.0 \
    AB_START_WAIT=1
HEALTHCHECK CMD ["/bin/bash","-c","curl -fs http://localhost:${HEALTHCHECK_PORT:-9010}/health || exit 1"]
ENTRYPOINT ["/workspace/entrypoint.sh"]
