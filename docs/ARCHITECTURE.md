# Architecture

This document describes the architecture of OpenCode on IM.

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         OpenCode                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                    Plugin System                           │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │              opencode-on-im Plugin                   │  │  │
│  │  │                                                      │  │  │
│  │  │  ┌──────────┐  ┌──────────┐  ┌──────────────────┐  │  │  │
│  │  │  │  Tools   │  │  State   │  │  Event Handler   │  │  │  │
│  │  │  │ im.start │  │ bindings │  │ session.created  │  │  │  │
│  │  │  │ im.stop  │  │ codes    │  │ message.part.*   │  │  │  │
│  │  │  │ im.bind  │  │ bot      │  │ session.idle     │  │  │  │
│  │  │  │ im.send  │  │ client   │  │ command.executed │  │  │  │
│  │  │  └──────────┘  └──────────┘  └──────────────────┘  │  │  │
│  │  │                      │                              │  │  │
│  │  └──────────────────────┼──────────────────────────────┘  │  │
│  └─────────────────────────┼─────────────────────────────────┘  │
└────────────────────────────┼────────────────────────────────────┘
                             │
                             │ Telegram Bot API (grammy)
                             ▼
                    ┌────────────────┐
                    │    Telegram    │
                    │    Servers     │
                    └────────────────┘
                             │
                             ▼
                    ┌────────────────┐
                    │  Telegram App  │
                    │  (User Phone)  │
                    └────────────────┘
```

## Components

### 1. Plugin Entry (`index.ts`)

The main plugin module that:
- Exports the `OpenCodeOnImPlugin` as default
- Registers 6 tools with OpenCode (`im.start`, `im.stop`, `im.status`, `im.bind`, `im.unbind`, `im.send`)
- Captures the running OpenCode server URL (`serverUrl`) for `/web`
- Handles OpenCode events and forwards key moments to Telegram
- Manages the lifecycle of the Telegram bot

### 2. State Manager (`state.ts`)

Centralized in-memory state management:

```typescript
interface PluginState {
  bot: Bot | null;              // Grammy bot instance
  token: string | null;         // Telegram bot token
  client: OpencodeClient | null; // OpenCode SDK client
  serverUrl: string | null;      // OpenCode server URL (for /web)
  pendingCodes: Map<string, PendingCode>;  // Verification codes
  bindings: Map<string, Binding>;          // User bindings (persisted)
  activeSessionId: string | null;          // Current session
  pendingResponses: Map<string, PendingResponse>;  // Message buffers
  processedMessages: Set<string>;          // Deduplication set
  pendingPermissions: Map<string, PendingPermission>; // Permission requests
  sessionStatus: SessionStatusState | null; // Latest session status snapshot
  sessionTodos: Map<string, TodoItem[]>;   // Todo snapshots per session
}
```

Bindings are persisted to disk at `$OPENCODE_HOME/opencode-on-im/bindings.json`.

### 3. Telegram Bot (`telegram/bot.ts`)

Grammy-based bot implementation:
- DM-only (private chat) to avoid accidental group exposure
- Handles binding (`/start` + verification code)
- Forwards normal text messages (non-`/` prefixed) as OpenCode prompts
- Provides slash commands for remote control (`/help`, `/status`, `/web`, `/session ...`, `/approve`, etc.)

### 4. Standalone Mode (`standalone.ts`)

For testing without OpenCode plugin context:
- Creates its own OpenCode client
- Subscribes to OpenCode events via SSE
- Manages sessions independently
- Useful for development and debugging

## Data Flow

### Binding Flow

```
User                    Telegram Bot              OpenCode
  │                          │                       │
  │  /start                  │                       │
  │ ─────────────────────────▶                       │
  │  "Enter verification     │                       │
  │   code"                  │                       │
  │ ◀─────────────────────────                       │
  │                          │                       │
  │                          │      im.bind          │
  │                          │ ◀─────────────────────│
  │                          │   code: "abc123xyz0"  │
  │                          │ ─────────────────────▶│
  │                          │                       │
  │  "abc123xyz0"            │                       │
  │ ─────────────────────────▶                       │
  │                          │  validateCode()       │
  │                          │  addBinding()         │
  │  "✅ Bound successfully!"│                       │
  │ ◀─────────────────────────                       │
```

### Message Flow (User → AI)

```
User                    Telegram Bot              OpenCode
  │                          │                       │
  │  "How do I..."           │                       │
  │ ─────────────────────────▶                       │
  │                          │  promptAsync()        │
  │                          │ ─────────────────────▶│
  │                          │                       │
  │                          │  message.part.updated │
  │                          │ ◀─────────────────────│
  │                          │  (accumulate text)    │
  │                          │                       │
  │                          │  session.idle         │
  │                          │ ◀─────────────────────│
  │  "AI Response..."        │  sendToAllBound()     │
  │ ◀─────────────────────────                       │
```

## Event Handling

The plugin subscribes to OpenCode events:

| Event | Handler Behavior |
|-------|------------------|
| `session.created` | Store active session ID |
| `session.status` | Track busy/idle/retry and notify key moments |
| `todo.updated` | Track todo progress and notify |
| `permission.updated` | Track permission requests and notify with `/approve` hint |
| `session.error` | Forward session errors |
| `message.updated` | Forward assistant errors |
| `message.part.updated` | Accumulate text deltas; forward tool outputs and tool errors |
| `session.idle` | Flush accumulated assistant text to Telegram users |
| `command.executed` | Notify users of command execution |

### Message Accumulation

AI responses are streamed as `message.part.updated` events with deltas. The plugin:

1. Accumulates text in `pendingResponses` map
2. On `session.idle`, flushes complete message to users
3. Uses `processedMessages` set for deduplication
4. Truncates messages > 4000 chars (Telegram limit)

## Security Considerations

### Verification Codes

- 10-character alphanumeric codes (a-z, 0-9)
- 1-minute expiry (prevents replay attacks)
- Single-use (deleted after validation)
- Regex validated: `/^[a-z0-9]{10}$/`

### User Binding

- Bindings are persisted to disk (`$OPENCODE_HOME/opencode-on-im/bindings.json`)
- Bot restart does not require re-binding
- No authentication token storage

### Chat Scope

- Telegram interactions are restricted to private chats (`ctx.chat.type === "private"`)

### Message Handling

- Messages truncated to 4000 chars (Telegram limit)
- Tool outputs summarized if > 1000 chars
- No sensitive data logging

## Limitations

- **Global active session** - All bound users share the same `activeSessionId` (but it can be switched via `/session use`)
- **Polling only** - No webhook support yet
- **No rate limiting** - Relies on Telegram's limits
- **Output size limits** - Telegram messages and tool outputs are truncated/summarized
