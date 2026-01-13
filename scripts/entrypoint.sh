#!/bin/bash
set -e

if [ ! -f /data/config.yaml ]; then
    echo "First run detected. Running setup wizard..."
    opencode-on-im setup --config /data/config.yaml
fi

if [ -n "$RESIDENTIAL_PROXY_URL" ]; then
    echo "Configuring proxy..."
    export HTTP_PROXY="$RESIDENTIAL_PROXY_URL"
    export HTTPS_PROXY="$RESIDENTIAL_PROXY_URL"
    export http_proxy="$RESIDENTIAL_PROXY_URL"
    export https_proxy="$RESIDENTIAL_PROXY_URL"
fi

exec "$@"
