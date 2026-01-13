# OpenCode Cloudify

> **Connect OpenCode to Telegram & DingTalk** — Manage your AI coding assistant from anywhere.

[![Deploy to DigitalOcean](https://www.deploytodo.com/do-btn-blue.svg)](https://cloud.digitalocean.com/apps/new?repo=https://github.com/opencode-cloudify/opencode-cloudify&refcode=YOUR_AFFILIATE_CODE)

[![PyPI version](https://badge.fury.io/py/opencode-on-im.svg)](https://pypi.org/project/opencode-on-im/)
[![Docker](https://img.shields.io/docker/v/opencodecloudify/cloudify)](https://hub.docker.com/r/opencodecloudify/cloudify)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## What is this?

OpenCode Cloudify turns your OpenCode AI coding assistant into a **24/7 cloud-based AI employee** that you can control from your phone via Telegram or DingTalk.

**Key Features:**

- **Multi-Instance Management** — Control multiple OpenCode instances from one chat
- **Real-time Notifications** — Get updates when AI completes tasks
- **Mobile-First** — Full CLI access via Web Terminal on your phone
- **Team Collaboration** — Multiple users can share access to instances
- **Code as Images** — Long code blocks rendered beautifully for mobile viewing

---

## Quick Start

### Option 1: Docker (Recommended)

```bash
docker run -d \
  -e TELEGRAM_TOKEN=your_bot_token \
  -v cloudify-data:/data \
  -p 7681:7681 \
  opencodecloudify/cloudify:latest
```

### Option 2: pip

```bash
pip install opencode-on-im
opencode-on-im setup
opencode-on-im run
```

---

## One-Click Cloud Deploy

Want 24/7 uptime without keeping your laptop open?

[![Deploy to DigitalOcean](https://www.deploytodo.com/do-btn-blue.svg)](https://cloud.digitalocean.com/apps/new?repo=https://github.com/opencode-cloudify/opencode-cloudify&refcode=YOUR_AFFILIATE_CODE)

> New users get **$200 free credit** for 60 days!

---

## Documentation

- [Setup Guide](docs/SETUP_GUIDE.md)
- [Configuration Reference](docs/CONFIGURATION.md)
- [Telegram Bot Setup](docs/TELEGRAM_SETUP.md)
- [DingTalk Setup](docs/DINGTALK_SETUP.md)
- [Proxy Best Practices](docs/PROXY_BEST_PRACTICE.md)

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

---

## Architecture

```
┌─────────────────────────────────────────┐
│           OpenCode Cloudify             │
├─────────────────────────────────────────┤
│  ┌─────────┐  ┌─────────┐  ┌─────────┐ │
│  │Telegram │  │DingTalk │  │  ttyd   │ │
│  │ Adapter │  │ Adapter │  │  (Web)  │ │
│  └────┬────┘  └────┬────┘  └────┬────┘ │
│       └────────────┼────────────┘      │
│                    ▼                    │
│         ┌──────────────────┐           │
│         │  Session Manager │           │
│         └────────┬─────────┘           │
│                  ▼                      │
│         ┌──────────────────┐           │
│         │   OpenCode SDK   │           │
│         └──────────────────┘           │
└─────────────────────────────────────────┘
```

---

## Using ChatGPT Plus in the Cloud?

If you're using your ChatGPT Plus subscription with OpenCode in the cloud, you may encounter IP blocks from OpenAI.

**Solution:** Use a static residential proxy to make your cloud server appear as a home connection.

[Learn more about proxy setup →](docs/PROXY_BEST_PRACTICE.md)

---

## Contributing

Contributions welcome! Please read [CONTRIBUTING.md](CONTRIBUTING.md) first.

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

## Acknowledgments

- [OpenCode](https://github.com/anomalyco/opencode) — The amazing AI coding assistant
- [aiogram](https://docs.aiogram.dev/) — Async Telegram bot framework
- [ttyd](https://github.com/tsl0922/ttyd) — Terminal over web
