#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

usage() {
    echo "OpenCode Plugin Test Environment"
    echo ""
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  start     Build and start the test environment"
    echo "  stop      Stop the test environment"
    echo "  shell     Open a shell in the running container"
    echo "  logs      Show container logs"
    echo "  rebuild   Rebuild the container image"
    echo "  clean     Remove all test environment data"
    echo ""
}

start_env() {
    mkdir -p "$SCRIPT_DIR/workspace"
    cd "$SCRIPT_DIR"
    docker compose up -d --build
    echo ""
    echo "Test environment started!"
    echo "Run: $0 shell  - to open an interactive shell"
}

stop_env() {
    cd "$SCRIPT_DIR"
    docker compose down
    echo "Test environment stopped."
}

open_shell() {
    docker exec -it opencode-plugin-test /bin/bash
}

show_logs() {
    cd "$SCRIPT_DIR"
    docker compose logs -f
}

rebuild_env() {
    cd "$SCRIPT_DIR"
    docker compose build --no-cache
    echo "Rebuild complete."
}

clean_env() {
    cd "$SCRIPT_DIR"
    docker compose down -v 2>/dev/null || true
    rm -rf "$SCRIPT_DIR/workspace"
    echo "Test environment cleaned."
}

case "${1:-}" in
    start)
        start_env
        ;;
    stop)
        stop_env
        ;;
    shell)
        open_shell
        ;;
    logs)
        show_logs
        ;;
    rebuild)
        rebuild_env
        ;;
    clean)
        clean_env
        ;;
    *)
        usage
        exit 1
        ;;
esac
