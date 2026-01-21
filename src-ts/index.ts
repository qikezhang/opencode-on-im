import type { Plugin } from "@opencode-ai/plugin";
import { tool } from "@opencode-ai/plugin/tool";
import { z } from "zod/v4";
import {
  getState,
  createPendingCode,
  getBindings,
  removeBinding,
} from "./state.js";

function formatTodosLine(todos: Array<{ status: string }>): string {
  const total = todos.length;
  const done = todos.filter((t) => t.status === "completed").length;
  return `${done}/${total}`;
}
import { startBot, stopBot, sendToAllBound } from "./telegram/bot.js";

interface TextPart {
  id: string;
  sessionID: string;
  messageID: string;
  type: "text";
  text: string;
}

interface ToolPart {
  id: string;
  sessionID: string;
  messageID: string;
  type: "tool";
  callID?: string;
  tool: string;
  state: { type?: string; status?: string; output?: string; error?: string };
}

type Part = TextPart | ToolPart | { type: string; [key: string]: unknown };

interface MessagePartUpdatedEvent {
  type: "message.part.updated";
  properties: {
    part: Part;
    delta?: string;
  };
}

interface SessionIdleEvent {
  type: "session.idle";
  properties: {
    sessionID: string;
  };
}

interface SessionCreatedEvent {
  type: "session.created";
  properties: {
    info?: { id?: string };
  };
}

interface CommandExecutedEvent {
  type: "command.executed";
  properties: {
    name: string;
    sessionID: string;
    arguments: string;
  };
}

interface PermissionUpdatedEvent {
  type: "permission.updated";
  properties: {
    id: string;
    sessionID: string;
    title: string;
    type: string;
    pattern?: string | string[];
    time?: { created: number };
    metadata?: Record<string, unknown>;
  };
}

interface SessionStatusEvent {
  type: "session.status";
  properties: {
    sessionID: string;
    status:
      | { type: "idle" }
      | { type: "busy" }
      | { type: "retry"; attempt: number; message: string; next: number };
  };
}

interface TodoUpdatedEvent {
  type: "todo.updated";
  properties: {
    sessionID: string;
    todos: Array<{ id: string; content: string; status: string; priority: string }>;
  };
}

interface SessionErrorEvent {
  type: "session.error";
  properties: {
    sessionID?: string;
    error?: { name: string; data?: { message?: string }; message?: string };
  };
}

interface MessageUpdatedEvent {
  type: "message.updated";
  properties: {
    info?: {
      role?: string;
      sessionID?: string;
      summary?: boolean;
      error?: { name?: string; data?: { message?: string }; message?: string };
      tokens?: { output?: number };
      cost?: number;
      finish?: string;
    };
  };
}

export const OpenCodeOnImPlugin: Plugin = async ({ client, serverUrl }) => {
  const state = getState();
  state.client = client;
  state.serverUrl = serverUrl?.toString() || null;

  return {
    event: async ({ event }) => {
      const evt = event as { type: string; properties?: Record<string, unknown> };

      if (evt.type === "session.created") {
        const e = evt as unknown as SessionCreatedEvent;
        if (!state.activeSessionId && e.properties?.info?.id) {
          state.activeSessionId = e.properties.info.id;
        }
      }

      if (evt.type === "session.status" && state.bot && state.bindings.size > 0) {
        const e = evt as unknown as SessionStatusEvent;
        const status = e.properties.status;
        state.sessionStatus = {
          sessionID: e.properties.sessionID,
          status: status.type === "retry" ? "retry" : status.type,
          retry: status.type === "retry" ? { attempt: status.attempt, message: status.message, next: status.next } : undefined,
          updatedAt: Date.now(),
        };

        if (status.type === "retry") {
          try {
            await sendToAllBound(`[Retry] attempt=${status.attempt} next=${Math.round(status.next / 1000)}s\n${status.message}`);
          } catch {}
        }

        if (status.type === "idle") {
          try {
            await sendToAllBound(`[Status] session idle (${e.properties.sessionID.slice(0, 8)}...)`);
          } catch {}
        }
      }

      if (evt.type === "todo.updated" && state.bot && state.bindings.size > 0) {
        const e = evt as unknown as TodoUpdatedEvent;
        state.sessionTodos.set(e.properties.sessionID, e.properties.todos);

        const todos = e.properties.todos;
        if (todos.length > 0) {
          const inProgress = todos.find((t) => t.status === "in_progress");
          const line = `[Todo] ${formatTodosLine(todos)}${inProgress ? ` | in_progress: ${inProgress.content}` : ""}`;
          try {
            await sendToAllBound(line);
          } catch {}
        }
      }

      if (evt.type === "permission.updated" && state.bot && state.bindings.size > 0) {
        const e = evt as unknown as PermissionUpdatedEvent;
        state.pendingPermissions.set(e.properties.id, {
          id: e.properties.id,
          sessionID: e.properties.sessionID,
          title: e.properties.title,
          type: e.properties.type,
          pattern: e.properties.pattern,
          time: e.properties.time,
        });

        try {
          const short = e.properties.id.slice(0, 8);
          await sendToAllBound(
            `[Permission] ${e.properties.title}\n` +
              `id=${e.properties.id}\n` +
              `Approve: /approve ${short} once|always|reject`
          );
        } catch {}
      }

      if (evt.type === "session.error" && state.bot && state.bindings.size > 0) {
        const e = evt as unknown as SessionErrorEvent;
        const msg = e.properties.error?.data?.message || e.properties.error?.message || e.properties.error?.name || "Unknown error";
        try {
          await sendToAllBound(`[Error] ${msg}`);
        } catch {}
      }

      if (evt.type === "message.updated" && state.bot && state.bindings.size > 0) {
        const e = evt as unknown as MessageUpdatedEvent;
        const info = e.properties.info;
        if (info?.role === "assistant" && info.error) {
          const msg = info.error.data?.message || info.error.message || info.error.name || "Unknown error";
          try {
            await sendToAllBound(`[Assistant Error] ${msg}`);
          } catch {}
        }
      }

      if (evt.type === "message.part.updated" && state.bot && state.bindings.size > 0) {
        const e = evt as unknown as MessagePartUpdatedEvent;
        const part = e.properties?.part;

        if (part?.type === "text") {
          const textPart = part as TextPart;
          const key = `${textPart.sessionID}:${textPart.messageID}`;

          if (!state.pendingResponses.has(key)) {
            state.pendingResponses.set(key, {
              sessionId: textPart.sessionID,
              textBuffer: "",
              lastUpdate: Date.now(),
            });
          }

          const pending = state.pendingResponses.get(key)!;
          if (e.properties.delta) {
            pending.textBuffer += e.properties.delta;
          } else {
            pending.textBuffer = textPart.text;
          }
          pending.lastUpdate = Date.now();
        }

        if (part?.type === "tool") {
          const toolPart = part as ToolPart;
          const stateType = toolPart.state?.type || toolPart.state?.status;

          if (stateType === "error" && toolPart.state?.error) {
            try {
              await sendToAllBound(`[Tool Error: ${toolPart.tool}]\n${toolPart.state.error}`);
            } catch {}
          }

          if ((stateType === "completed" || stateType === "done") && toolPart.state.output) {
            const output = toolPart.state.output;
            if (output.length > 100) {
              const summary = output.length > 1000 ? output.slice(0, 1000) + "..." : output;
              try {
                await sendToAllBound(`[Tool: ${toolPart.tool}]\n${summary}`);
              } catch {}
            }
          }
        }
      }

      if (evt.type === "session.idle" && state.bot && state.bindings.size > 0) {
        const e = evt as unknown as SessionIdleEvent;
        const sessionId = e.properties?.sessionID;

        for (const [key, pending] of state.pendingResponses.entries()) {
          if (pending.sessionId === sessionId && pending.textBuffer.length > 0) {
            if (!state.processedMessages.has(key)) {
              state.processedMessages.add(key);
              const text = pending.textBuffer;
              if (text.length > 0) {
                try {
                  const message = text.length > 4000 
                    ? text.slice(0, 4000) + "\n\n[Truncated...]"
                    : text;
                  await sendToAllBound(message);
                } catch {}
              }
            }
            state.pendingResponses.delete(key);
          }
        }

        if (state.processedMessages.size > 100) {
          const arr = Array.from(state.processedMessages);
          arr.slice(0, 50).forEach((k) => state.processedMessages.delete(k));
        }
      }

      if (evt.type === "command.executed" && state.bot && state.bindings.size > 0) {
        const e = evt as unknown as CommandExecutedEvent;
        try {
          await sendToAllBound(`[Command] ${e.properties.name} ${e.properties.arguments}`);
        } catch {}
      }
    },

    tool: {
      "im.start": tool({
        description: "Start the Telegram bot for remote access",
        args: {
          token: z.string().optional().describe("Telegram bot token (uses TELEGRAM_TOKEN env if not provided)"),
        },
        async execute({ token }) {
          const botToken = token || process.env.TELEGRAM_TOKEN;
          if (!botToken) {
            return "Error: No token provided. Set TELEGRAM_TOKEN or pass token parameter.";
          }
          try {
            await startBot(botToken);
            return "Telegram bot started successfully. Users can now bind using verification codes.";
          } catch (error) {
            return `Error: ${error instanceof Error ? error.message : "Unknown error"}`;
          }
        },
      }),

      "im.stop": tool({
        description: "Stop the Telegram bot",
        args: {},
        async execute() {
          try {
            await stopBot();
            return "Telegram bot stopped.";
          } catch (error) {
            return `Error: ${error instanceof Error ? error.message : "Unknown error"}`;
          }
        },
      }),

      "im.status": tool({
        description: "Get the current status of the Telegram bot and bound users",
        args: {},
        async execute() {
          const state = getState();
          const bindings = getBindings();

          if (!state.bot) {
            return "Bot is not running. Use im.start to start it.";
          }

          const sessionInfo = state.activeSessionId
            ? `Active session: ${state.activeSessionId}`
            : "No active session";

          if (bindings.length === 0) {
            return `Bot is running.\n${sessionInfo}\n\nNo users bound yet. Use im.bind to generate a verification code.`;
          }

          const userList = bindings
            .map((b) => `- ${b.telegramUsername || b.telegramUserId} (bound ${new Date(b.boundAt).toLocaleString()})`)
            .join("\n");

          return `Bot is running.\n${sessionInfo}\n\nBound users (${bindings.length}):\n${userList}`;
        },
      }),

      "im.bind": tool({
        description: "Generate a 10-character verification code for binding Telegram users (valid for 1 minute)",
        args: {},
        async execute() {
          const state = getState();
          if (!state.bot) {
            return "Error: Bot is not running. Use im.start first.";
          }

          const code = createPendingCode();
          return `Verification code: ${code}\n\nThis code expires in 1 minute. Send this code to the Telegram bot to complete binding.`;
        },
      }),

      "im.unbind": tool({
        description: "Remove a bound Telegram user",
        args: {
          userId: z.string().describe("Telegram user ID to unbind"),
        },
        async execute({ userId }) {
          if (removeBinding(userId)) {
            return `User ${userId} has been unbound.`;
          }
          return `User ${userId} was not bound.`;
        },
      }),

      "im.send": tool({
        description: "Send a message to all bound Telegram users",
        args: {
          message: z.string().describe("Message to send"),
        },
        async execute({ message }) {
          try {
            const count = await sendToAllBound(message);
            return `Message sent to ${count} user(s).`;
          } catch (error) {
            return `Error: ${error instanceof Error ? error.message : "Unknown error"}`;
          }
        },
      }),
    },
  };
};

export default OpenCodeOnImPlugin;
