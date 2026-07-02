FROM python:3.12-slim

# Unbuffered stdout/stderr so sync progress shows up in logs (mlog) live.
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
        ffmpeg ca-certificates curl \
    && rm -rf /var/lib/apt/lists/*

ARG TARGETARCH=amd64
ARG SUPERCRONIC_VERSION=v0.2.33
RUN curl -fsSL -o /usr/local/bin/supercronic \
        "https://github.com/aptible/supercronic/releases/download/${SUPERCRONIC_VERSION}/supercronic-linux-${TARGETARCH}" \
    && chmod +x /usr/local/bin/supercronic

WORKDIR /app
COPY orchestrator/pyproject.toml ./
COPY orchestrator/src ./src
RUN pip install --no-cache-dir .

COPY config.yaml /app/config.yaml
COPY orchestrator/crontab /app/crontab

CMD ["supercronic", "/app/crontab"]
