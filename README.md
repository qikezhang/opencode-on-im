# OpenCode on IM

> Connect OpenCode to Telegram — Control your AI coding assistant remotely.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## What is this?

OpenCode on IM is an **OpenCode plugin** that lets you interact with your AI coding assistant via Telegram. Send messages from your phone, receive AI responses, and monitor your coding sessions remotely.

## Features

- **Remote Access** — Control OpenCode from Telegram on any device
- **Key Moment Notifications** — Get notified when tasks complete, permissions are needed, errors occur, or todo milestones are reached
- **Secure Binding** — 10-character verification codes (1 minute expiry)
- **Multi-User** — Multiple Telegram users can bind to one instance
- **Bidirectional** — Send prompts to AI, receive responses and status updates
- **Slash Commands** — Full session control via Telegram commands
- **Permission Approval** — Approve/reject AI permission requests directly from Telegram
- **Persistent Bindings** — User bindings survive bot/OpenCode restarts

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

Bindings are persisted to `$OPENCODE_HOME/opencode-on-im/bindings.json` and survive bot restarts.

## Telegram Commands

Once bound, use these commands in your Telegram chat with the bot:

| Command | Description |
|---------|-------------|
| `/start` | Begin binding flow (for new users) |
| `/help` | Show all available commands |
| `/status` | Show connection status, active session, todos, pending permissions |
| `/web` | Get the web interface URL |
| `/session list` | List all sessions |
| `/session use <n\|id>` | Switch to session by number or ID prefix |
| `/session new` | Create a new session |
| `/approve <id> once\|always\|reject` | Respond to a permission request |
| `/agent cycle` | Cycle to next agent |
| `/interrupt` | Interrupt the current session |
| `/prompt clear` | Clear the TUI prompt |
| `/prompt submit` | Submit the TUI prompt |
| `/page up\|down\|half-up\|half-down\|first\|last` | Scroll session view |

**Default behavior**: Any text message (not starting with `/`) is sent to OpenCode as a prompt.

## Notifications

The plugin sends you Telegram notifications for key moments:

| Event | Notification |
|-------|--------------|
| **Task Complete** | Session becomes idle after being busy |
| **Permission Needed** | AI needs approval (with `/approve` hint) |
| **Retry/Failure** | Session enters retry state or fails |
| **Todo Progress** | All todos completed, or first todo starts |
| **Tool Errors** | Tool execution errors |

## Permission Approval Flow

When the AI needs permission for an action:

1. You receive a Telegram message like:
   ```
   🔐 Permission Required
   Tool: bash
   Path: /path/to/file
   Reply: /approve abc123 once|always|reject
   ```

2. Reply with one of:
   - `/approve abc123 once` — Allow this one time
   - `/approve abc123 always` — Always allow this action
   - `/approve abc123 reject` — Deny the request

3. You can use just the ID prefix (e.g., `/approve abc once`)

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
