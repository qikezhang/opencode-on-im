# OpenCode Cloudify - Multi-stage Docker build
# Target: < 500MB final image
# Components: OpenCode + opencode-on-im + ttyd + s6-overlay

ARG PYTHON_VERSION=3.11
ARG S6_OVERLAY_VERSION=3.1.6.2
ARG TTYD_VERSION=1.7.4

# =============================================================================
# Stage 1: Python dependencies builder
# =============================================================================
FROM python:${PYTHON_VERSION}-slim AS python-builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency files
COPY pyproject.toml ./
COPY src/ ./src/

# Build wheel with poetry-core, then install to /install
RUN pip install build && \
    python -m build --wheel --outdir /tmp/dist . && \
    pip install --target=/install /tmp/dist/*.whl

# =============================================================================
# Stage 2: ttyd binary (pre-built from GitHub releases)
# =============================================================================
FROM alpine:3.19 AS ttyd-builder

ARG TTYD_VERSION
ARG TARGETARCH

# Download pre-built ttyd binary
RUN apk add --no-cache curl && \
    ARCH=$(case ${TARGETARCH} in \
        amd64) echo "x86_64" ;; \
        arm64) echo "aarch64" ;; \
        *) echo "x86_64" ;; \
    esac) && \
    curl -fsSL "https://github.com/tsl0922/ttyd/releases/download/${TTYD_VERSION}/ttyd.${ARCH}" \
        -o /ttyd && \
    chmod +x /ttyd

# =============================================================================
# Stage 3: s6-overlay downloader
# =============================================================================
FROM alpine:3.19 AS s6-builder

ARG S6_OVERLAY_VERSION
ARG TARGETARCH

WORKDIR /s6

# Download s6-overlay
RUN apk add --no-cache curl xz && \
    ARCH=$(case ${TARGETARCH} in \
        amd64) echo "x86_64" ;; \
        arm64) echo "aarch64" ;; \
        *) echo "x86_64" ;; \
    esac) && \
    # Download noarch (scripts)
    curl -fsSL "https://github.com/just-containers/s6-overlay/releases/download/v${S6_OVERLAY_VERSION}/s6-overlay-noarch.tar.xz" \
        -o /tmp/s6-noarch.tar.xz && \
    # Download arch-specific (binaries)
    curl -fsSL "https://github.com/just-containers/s6-overlay/releases/download/v${S6_OVERLAY_VERSION}/s6-overlay-${ARCH}.tar.xz" \
        -o /tmp/s6-arch.tar.xz && \
    # Extract to /s6 for later copying
    mkdir -p /s6-root && \
    tar -C /s6-root -Jxpf /tmp/s6-noarch.tar.xz && \
    tar -C /s6-root -Jxpf /tmp/s6-arch.tar.xz

# =============================================================================
# Stage 4: Final runtime image
# =============================================================================
FROM python:${PYTHON_VERSION}-slim AS runtime

# Labels
LABEL org.opencontainers.image.title="OpenCode Cloudify" \
      org.opencontainers.image.description="Cloud-native AI coding assistant with IM integration" \
      org.opencontainers.image.source="https://github.com/opencode-cloudify/opencode-on-im" \
      org.opencontainers.image.licenses="MIT"

# s6-overlay environment
ENV S6_KEEP_ENV=1 \
    S6_BEHAVIOUR_IF_STAGE2_FAILS=2 \
    S6_CMD_WAIT_FOR_SERVICES_MAXTIME=30000

# Application environment
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    OPENCODE_IM__DATA_DIR=/data \
    OPENCODE_PORT=4096 \
    TTYD_PORT=7681 \
    PATH="/app/bin:${PATH}"

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    # Fonts for image rendering
    fonts-dejavu-core \
    fonts-liberation \
    # Terminal utilities
    bash \
    procps \
    curl \
    ca-certificates \
    # Node.js for OpenCode (if needed)
    nodejs \
    npm \
    && rm -rf /var/lib/apt/lists/* \
    # Create non-root user
    && useradd -m -s /bin/bash -u 1000 cloudify \
    && mkdir -p /data /app \
    && chown -R cloudify:cloudify /data /app

# Copy s6-overlay
COPY --from=s6-builder /s6-root/ /

# Copy ttyd binary
COPY --from=ttyd-builder /ttyd /usr/local/bin/ttyd

# Copy Python packages
COPY --from=python-builder /install /usr/local/lib/python3.11/site-packages

# Copy application source
COPY src/ /app/src/

# Copy s6 service definitions
COPY docker/rootfs/ /

# Make scripts executable
RUN chmod +x /etc/s6-overlay/s6-rc.d/*/run 2>/dev/null || true && \
    chmod +x /etc/s6-overlay/s6-rc.d/*/finish 2>/dev/null || true && \
    chmod +x /etc/s6-overlay/scripts/* 2>/dev/null || true && \
    chmod +x /etc/cont-init.d/* 2>/dev/null || true

# Verify installations
RUN python -c "import opencode_on_im; print('opencode-on-im OK')" && \
    ttyd --version && \
    echo "All components verified"

# Data volume
VOLUME ["/data"]

# Expose ports
# 7681: ttyd (Web Terminal)
# 4096: OpenCode API (internal, proxied via bot)
EXPOSE 7681

# Health check - uses comprehensive script checking all services
HEALTHCHECK --interval=30s --timeout=15s --start-period=90s --retries=3 \
    CMD /etc/s6-overlay/scripts/healthcheck || exit 1

# s6-overlay init
ENTRYPOINT ["/init"]
