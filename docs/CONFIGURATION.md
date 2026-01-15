# Configuration Reference

Complete reference for all configuration options.

## Configuration Methods

Configuration can be provided via:

1. **Environment variables** (highest priority)
2. **Config file** (`config.yaml`)
3. **Default values**

## Environment Variables

### Core Settings

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENCODE_IM__DATA_DIR` | `/data` | Data directory for databases and files |
| `OPENCODE_PORT` | `4096` | OpenCode API port |
| `OPENCODE_HOST` | `127.0.0.1` | OpenCode API host |
| `TTYD_PORT` | `7681` | Web terminal port |
| `OPENCODE_IM__SECRET_KEY` | `change-me-in-production` | Secret key for sessions |

### Telegram

| Variable | Default | Description |
|----------|---------|-------------|
| `TELEGRAM_TOKEN` | - | Bot API token from BotFather |
| `TELEGRAM_PARSE_MODE` | `MarkdownV2` | Message parse mode |

### DingTalk

| Variable | Default | Description |
|----------|---------|-------------|
| `DINGTALK_APP_KEY` | - | Application key |
| `DINGTALK_APP_SECRET` | - | Application secret |
| `DINGTALK_AGENT_ID` | - | Agent ID (optional) |

### Proxy

| Variable | Default | Description |
|----------|---------|-------------|
| `PROXY_ENABLED` | `false` | Enable proxy |
| `PROXY_URL` | - | Proxy URL (e.g., `socks5://user:pass@host:port`) |

### Behavior

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENCODE_IM__MESSAGE_IMAGE_THRESHOLD` | `10` | Lines before rendering as image |
| `OPENCODE_IM__MAX_OFFLINE_MESSAGES` | `20` | Max queued offline messages |
| `OPENCODE_IM__UPGRADE_CHECK_ENABLED` | `true` | Check for updates |

## Config File

Create `config.yaml` in your data directory:

```yaml
# Core settings
data_dir: /data
opencode_port: 4096
opencode_host: 127.0.0.1
web_terminal: ttyd
web_terminal_port: 7681

# Secret key (change in production!)
secret_key: your-secure-secret-key

# Telegram configuration
telegram:
  token: "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
  parse_mode: MarkdownV2

# DingTalk configuration
dingtalk:
  app_key: "your_app_key"
  app_secret: "your_app_secret"
  agent_id: "your_agent_id"

# Proxy configuration
proxy:
  enabled: true
  url: "socks5://user:pass@proxy.example.com:1080"

# Behavior
message_image_threshold: 10
max_offline_messages: 20

# Update checks
upgrade_check_enabled: true
upgrade_check_url: "https://api.opencode-cloudify.dev/v1/check-update"
```

## Docker Compose Example

```yaml
version: '3.8'
services:
  cloudify:
    image: opencodecloudify/cloudify:latest
    environment:
      # Required: At least one IM platform
      - TELEGRAM_TOKEN=${TELEGRAM_TOKEN}
      
      # Optional: DingTalk
      - DINGTALK_APP_KEY=${DINGTALK_APP_KEY}
      - DINGTALK_APP_SECRET=${DINGTALK_APP_SECRET}
      
      # Optional: Proxy for cloud servers
      - PROXY_ENABLED=true
      - PROXY_URL=socks5://user:pass@proxy:1080
      
      # Optional: Customization
      - OPENCODE_IM__MESSAGE_IMAGE_THRESHOLD=15
      - OPENCODE_IM__SECRET_KEY=${SECRET_KEY}
    volumes:
      - cloudify-data:/data
    ports:
      - "7681:7681"
    restart: unless-stopped

volumes:
  cloudify-data:
```

## Validation

Configuration is validated at startup. Invalid values will:

1. Log a warning
2. Fall back to defaults (if possible)
3. Exit with error (if required value is missing)

## Security Best Practices

1. **Never commit secrets** to version control
2. Use **environment variables** for sensitive values
3. Change the **secret_key** in production
4. Use **HTTPS** if exposing web terminal publicly
5. Consider **VPN** or **SSH tunnel** for web terminal access
