import type { Plugin } from "@opencode-ai/plugin";
import { tool } from "@opencode-ai/plugin/tool";
import { z } from "zod/v4";
import {
  getState,
  createPendingCode,
  getBindings,
  removeBinding,
} from "./state.js";
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
  tool: string;
  state: { type: string; output?: string };
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

export const OpenCodeOnImPlugin: Plugin = async ({ client }) => {
  const state = getState();
  state.client = client;

  return {
    event: async ({ event }) => {
      const evt = event as { type: string; properties?: Record<string, unknown> };

      if (evt.type === "session.created") {
        const e = evt as unknown as SessionCreatedEvent;
        if (e.properties?.info?.id) {
          state.activeSessionId = e.properties.info.id;
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
          if (toolPart.state?.type === "completed" && toolPart.state.output) {
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
