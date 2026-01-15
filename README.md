# OpenCode Cloudify

> **Connect OpenCode to Telegram & DingTalk** — Manage your AI coding assistant from anywhere.

[![PyPI version](https://badge.fury.io/py/opencode-on-im.svg)](https://pypi.org/project/opencode-on-im/)
[![Docker](https://img.shields.io/docker/v/opencodecloudify/cloudify)](https://hub.docker.com/r/opencodecloudify/cloudify)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Tests](https://img.shields.io/badge/tests-109%20passed-brightgreen)](https://github.com/opencode-cloudify/opencode-on-im)

---

## What is this?

OpenCode Cloudify turns your OpenCode AI coding assistant into a **24/7 cloud-based AI employee** that you can control from your phone via Telegram or DingTalk.

**Key Features:**

- **Multi-Instance Management** — Control multiple OpenCode instances from one chat
- **Real-time Notifications** — Get updates when AI completes tasks
- **Mobile-First** — Full CLI access via Web Terminal on your phone
- **Team Collaboration** — Multiple users can share access to instances
- **Code as Images** — Long code blocks rendered beautifully for mobile viewing
- **Auto-Reconnect** — Resilient SSE connections with exponential backoff

---

## Quick Start

### Option 1: Docker (Recommended)

```bash
docker run -d \
  --name opencode-cloudify \
  -e TELEGRAM_TOKEN=your_bot_token \
  -v cloudify-data:/data \
  -p 7681:7681 \
  opencodecloudify/cloudify:latest
```

### Option 2: Docker Compose

```yaml
version: '3.8'
services:
  cloudify:
    image: opencodecloudify/cloudify:latest
    environment:
      - TELEGRAM_TOKEN=${TELEGRAM_TOKEN}
    volumes:
      - cloudify-data:/data
    ports:
      - "7681:7681"
    restart: unless-stopped

volumes:
  cloudify-data:
```

```bash
export TELEGRAM_TOKEN=your_bot_token
docker-compose up -d
```

### Option 3: pip

```bash
pip install opencode-on-im
opencode-on-im setup
opencode-on-im run
```

---

## One-Click Cloud Deploy

Want 24/7 uptime without keeping your laptop open?

[![Deploy to DigitalOcean](https://www.deploytodo.com/do-btn-blue.svg)](https://cloud.digitalocean.com/apps/new?repo=https://github.com/opencode-cloudify/opencode-cloudify)

> New users get **$200 free credit** for 60 days!

---

## Commands

| Command | Description |
|---------|-------------|
| `/start` | Begin using the bot |
| `/status` | Current instance status |
| `/list` | List all bound instances |
| `/switch <name>` | Switch active instance |
| `/web` | Get Web Terminal link |
| `/cancel` | Cancel current task |
| `/help` | Show help message |

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│              OpenCode Cloudify                       │
├─────────────────────────────────────────────────────┤
│  ┌───────────┐  ┌───────────┐  ┌───────────┐       │
│  │ Telegram  │  │ DingTalk  │  │   ttyd    │       │
│  │  Adapter  │  │  Adapter  │  │   (Web)   │       │
│  └─────┬─────┘  └─────┬─────┘  └─────┬─────┘       │
│        └──────────────┼──────────────┘              │
│                       ▼                              │
│         ┌─────────────────────────┐                 │
│         │    Session Manager      │                 │
│         │  (SQLite + QR Binding)  │                 │
│         └───────────┬─────────────┘                 │
│                     ▼                                │
│         ┌─────────────────────────┐                 │
│         │    OpenCode Client      │                 │
│         │  (SSE + Auto-Reconnect) │                 │
│         └─────────────────────────┘                 │
└─────────────────────────────────────────────────────┘
```

---

## Documentation

- [Setup Guide](docs/SETUP_GUIDE.md) — Complete installation instructions
- [Configuration Reference](docs/CONFIGURATION.md) — All configuration options
- [Telegram Bot Setup](docs/TELEGRAM_SETUP.md) — Create and configure Telegram bot
- [DingTalk Setup](docs/DINGTALK_SETUP.md) — Create and configure DingTalk bot
- [Proxy Best Practices](docs/PROXY_BEST_PRACTICE.md) — Using residential proxies

---

## FAQ

### Why do I need a proxy?

If you're running OpenCode with ChatGPT Plus on a cloud server, OpenAI may block datacenter IPs. A residential proxy makes your server appear as a home connection.

### Can multiple users share one instance?

Yes! Multiple Telegram/DingTalk users can bind to the same OpenCode instance. Use the QR code binding flow.

### How do I switch between instances?

Use `/list` to see all bound instances, then `/switch <name>` to change the active one.

### Why are long messages sent as images?

Telegram has a 4096 character limit. Long code blocks are rendered as syntax-highlighted images for better mobile viewing.

### How do I access the full terminal?

Use `/web` to get a link to the ttyd web terminal. This gives you full CLI access from any browser.

### Is my data secure?

- All data is stored locally in your `/data` volume
- No data is sent to external servers (except your configured IM platform)
- Tokens are stored securely and never logged

---

## Using ChatGPT Plus in the Cloud?

If you're using your ChatGPT Plus subscription with OpenCode in the cloud, you may encounter IP blocks from OpenAI.

**Solution:** Use a static residential proxy to make your cloud server appear as a home connection.

[Learn more about proxy setup →](docs/PROXY_BEST_PRACTICE.md)

---

## Development

```bash
# Clone the repository
git clone https://github.com/opencode-cloudify/opencode-on-im
cd opencode-on-im

# Create virtual environment
uv venv .venv
source .venv/bin/activate

# Install dependencies
uv pip install -e "."
uv pip install pytest pytest-asyncio pytest-cov ruff mypy

# Run tests
PYTHONPATH=src pytest tests/ -v

# Lint
ruff check src/
```

---

## Contributing

Contributions welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) first.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

## Acknowledgments

- [OpenCode](https://github.com/opencode-ai/opencode) — The amazing AI coding assistant
- [aiogram](https://docs.aiogram.dev/) — Async Telegram bot framework
- [ttyd](https://github.com/tsl0922/ttyd) — Terminal over web
- [s6-overlay](https://github.com/just-containers/s6-overlay) — Process supervision
