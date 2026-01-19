# OpenCode on IM

> Connect OpenCode to Telegram — Control your AI coding assistant remotely.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## What is this?

OpenCode on IM is an **OpenCode plugin** that lets you interact with your AI coding assistant via Telegram. Send messages from your phone, receive AI responses, and monitor your coding sessions remotely.

## Features

- **Remote Access** — Control OpenCode from Telegram on any device
- **Secure Binding** — 10-character verification codes (1 minute expiry)
- **Multi-User** — Multiple Telegram users can bind to one instance
- **Bidirectional** — Send messages to AI, receive summaries back
- **Simple Tools** — Start/stop bot, manage bindings, send messages

## Quick Start

### 1. Install the Plugin

Add to your OpenCode config (`~/.config/opencode/opencode.json`):

```json
{
  "plugins": [
    "opencode-on-im@file:/path/to/opencode-on-im"
  ]
}
```

### 2. Set Telegram Token

Get a bot token from [@BotFather](https://t.me/botfather), then:

```bash
export TELEGRAM_TOKEN=your_bot_token
```

### 3. Use in OpenCode

```
> im.start                    # Start the bot
> im.bind                     # Get verification code
> im.status                   # Check status
> im.send message="Hello!"    # Send to all users
> im.stop                     # Stop the bot
```

## Available Tools

| Tool | Description |
|------|-------------|
| `im.start` | Start Telegram bot (token from env or param) |
| `im.stop` | Stop the bot |
| `im.status` | Show bot status and bound users |
| `im.bind` | Generate 10-char verification code (1 min expiry) |
| `im.unbind` | Remove a bound user by ID |
| `im.send` | Send message to all bound users |

## Binding Flow

1. Run `im.start` in OpenCode
2. Run `im.bind` to get a verification code
3. Send the code to your Telegram bot
4. Done! Now you can send messages to OpenCode via Telegram

## Development

```bash
# Install dependencies
npm install

# Build
npm run build

# Type check
npm run typecheck
```

### Docker Test Environment

An isolated Docker environment for testing without affecting your local OpenCode:

```bash
cd test-env
./test-env.sh start   # Start isolated test container
./test-env.sh shell   # Open shell in container
./test-env.sh stop    # Stop container
./test-env.sh clean   # Remove all test data
```

The test container uses a separate data directory (`/data/opencode`) that doesn't share data with the host system.

## License

MIT
