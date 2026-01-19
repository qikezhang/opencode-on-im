# OpenCode Plugin Test Environment
# Isolated container for testing opencode-on-im plugin without affecting host

FROM node:20-slim

LABEL maintainer="OpenCode Cloudify Team"
LABEL description="Isolated OpenCode test environment for TypeScript plugin development"

# Install dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    jq \
    unzip \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install bun
RUN curl -fsSL https://bun.sh/install | bash
ENV PATH="/root/.bun/bin:${PATH}"

# Create directories
# /data/opencode - isolated OpenCode data (NOT shared with host)
# /workspace - project workspace
# /plugin - plugin source
RUN mkdir -p /data/opencode /workspace /plugin /root/.local/bin

# Install OpenCode from anomalyco/opencode (v1.1.25)
ARG OPENCODE_VERSION=v1.1.25
ARG TARGETARCH
RUN ARCH=$([ "$TARGETARCH" = "arm64" ] && echo "arm64" || echo "x64") && \
    curl -fsSL "https://github.com/anomalyco/opencode/releases/download/${OPENCODE_VERSION}/opencode-linux-${ARCH}.tar.gz" -o /tmp/opencode.tar.gz && \
    tar -xzf /tmp/opencode.tar.gz -C /root/.local/bin && \
    chmod +x /root/.local/bin/opencode && \
    rm /tmp/opencode.tar.gz

ENV PATH="/root/.local/bin:${PATH}"

# Set OpenCode to use isolated data directory
ENV OPENCODE_HOME="/data/opencode"

WORKDIR /workspace

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD opencode --version || exit 1

CMD ["bash"]
