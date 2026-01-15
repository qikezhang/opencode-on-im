# Setup Guide

Complete guide for setting up OpenCode Cloudify.

## Prerequisites

- Python 3.11+
- Docker (for containerized deployment)
- Telegram Bot Token OR DingTalk App credentials

## Installation Methods

### Method 1: Docker (Recommended)

```bash
# Pull and run
docker run -d \
  --name opencode-cloudify \
  -e TELEGRAM_TOKEN=your_bot_token \
  -v cloudify-data:/data \
  -p 7681:7681 \
  opencodecloudify/cloudify:latest
```

### Method 2: Docker Compose

Create `docker-compose.yml`:

```yaml
version: '3.8'
services:
  cloudify:
    image: opencodecloudify/cloudify:latest
    container_name: opencode-cloudify
    environment:
      - TELEGRAM_TOKEN=${TELEGRAM_TOKEN}
      - OPENCODE_IM__DATA_DIR=/data
    volumes:
      - cloudify-data:/data
    ports:
      - "7681:7681"
    restart: unless-stopped

volumes:
  cloudify-data:
```

Run:
```bash
export TELEGRAM_TOKEN=your_bot_token
docker-compose up -d
```

### Method 3: pip Install

```bash
# Install
pip install opencode-on-im

# Interactive setup
opencode-on-im setup

# Run
opencode-on-im run
```

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `TELEGRAM_TOKEN` | Yes* | Telegram Bot API token |
| `DINGTALK_APP_KEY` | Yes* | DingTalk app key |
| `DINGTALK_APP_SECRET` | Yes* | DingTalk app secret |
| `OPENCODE_IM__DATA_DIR` | No | Data directory (default: `/data`) |
| `OPENCODE_PORT` | No | OpenCode API port (default: `4096`) |
| `TTYD_PORT` | No | Web terminal port (default: `7681`) |

*At least one IM platform is required.

### Config File

Create `config.yaml`:

```yaml
telegram:
  token: "your_bot_token"
  parse_mode: "MarkdownV2"

dingtalk:
  app_key: "your_app_key"
  app_secret: "your_app_secret"

proxy:
  enabled: false
  url: "socks5://user:pass@host:port"

message_image_threshold: 10
max_offline_messages: 20
```

## First Run

1. Start the service
2. Open Telegram and find your bot
3. Send `/start` to begin
4. The bot will guide you through binding an OpenCode instance

## Web Terminal Access

Access the web terminal at: `http://your-server:7681`

This provides full CLI access to your OpenCode instance from any browser.

## Troubleshooting

### Bot not responding

1. Verify your token is correct
2. Check logs: `docker logs opencode-cloudify`
3. Ensure port 7681 is accessible

### Connection issues

If using a cloud server, you may need a residential proxy. See [Proxy Best Practices](PROXY_BEST_PRACTICE.md).

## Next Steps

- [Telegram Bot Setup](TELEGRAM_SETUP.md)
- [DingTalk Setup](DINGTALK_SETUP.md)
- [Configuration Reference](CONFIGURATION.md)
