import { Bot } from "grammy";
import {
  getState,
  validateCode,
  addBinding,
  isUserBound,
} from "../state.js";

function splitMessage(text: string, maxLength: number): string[] {
  const chunks: string[] = [];
  let remaining = text;
  while (remaining.length > 0) {
    if (remaining.length <= maxLength) {
      chunks.push(remaining);
      break;
    }
    let splitAt = remaining.lastIndexOf("\n", maxLength);
    if (splitAt === -1 || splitAt < maxLength / 2) {
      splitAt = maxLength;
    }
    chunks.push(remaining.slice(0, splitAt));
    remaining = remaining.slice(splitAt).trimStart();
  }
  return chunks;
}

export async function startBot(token: string, options?: { polling?: boolean }): Promise<void> {
  const state = getState();

  if (state.bot) {
    throw new Error("Bot is already running");
  }

  const bot = new Bot(token);

  bot.catch((err) => {
    console.error("[opencode-on-im] Bot error:", err);
  });

  bot.command("start", async (ctx) => {
    const userId = String(ctx.from?.id);
    if (isUserBound(userId)) {
      await ctx.reply("You are already bound. Send a message to chat with AI.");
      return;
    }
    await ctx.reply(
      "Welcome! Please enter your 10-character verification code to bind."
    );
  });

  bot.command("status", async (ctx) => {
    const userId = String(ctx.from?.id);
    if (!isUserBound(userId)) {
      await ctx.reply("You are not bound. Use /start to begin.");
      return;
    }
    const connected = state.client ? "✅ Connected" : "❌ Not connected";
    const session = state.activeSessionId ? `Session: ${state.activeSessionId.slice(0, 8)}...` : "No session";
    await ctx.reply(`${connected}\n${session}\n\nSend a message to chat with AI.`);
  });

  bot.on("message:text", async (ctx) => {
    const text = ctx.message.text;
    const userId = String(ctx.from?.id);
    const username = ctx.from?.username;

    if (text.startsWith("/")) return;

    if (!isUserBound(userId)) {
      if (/^[a-z0-9]{10}$/.test(text)) {
        if (validateCode(text)) {
          addBinding(userId, username);
          console.log(`[opencode-on-im] Bound user ${userId}${username ? ` (@${username})` : ""}`);
          await ctx.reply("✅ Bound successfully! Send a message to chat with AI.");
          return;
        } else {
          await ctx.reply("Invalid or expired code. Please request a new one.");
          return;
        }
      }
      await ctx.reply("You are not bound. Please enter your verification code.");
      return;
    }

    if (!state.client) {
      await ctx.reply("⏳ Connecting to OpenCode...");
      return;
    }

    if (!state.activeSessionId) {
      await ctx.reply("No active session. Creating one...");
      try {
        const res = await state.client.session.create({});
        if (res.data) {
          state.activeSessionId = res.data.id;
        }
      } catch {
        await ctx.reply("Failed to create session.");
        return;
      }
    }

    try {
      console.log(`[opencode-on-im] Forwarding message from ${userId} to session ${state.activeSessionId}: ${text.slice(0, 200)}`);
      await state.client.session.promptAsync({
        path: { id: state.activeSessionId! },
        body: {
          parts: [{ type: "text", text }],
        },
      });
    } catch (error) {
      const errMsg = error instanceof Error ? error.message : "Unknown error";
      await ctx.reply(`Error: ${errMsg}`);
    }
  });

  state.bot = bot;
  state.token = token;

  if (options?.polling !== false) {
    bot.start({
      onStart: () => {
        console.log("[opencode-on-im] Telegram bot started (polling active)");
      },
      drop_pending_updates: true,
      timeout: 5,
    });
  } else {
    console.log("[opencode-on-im] Telegram bot created (polling disabled)");
  }

  await new Promise((resolve) => setTimeout(resolve, 500));
}

export async function stopBot(): Promise<void> {
  const state = getState();
  if (!state.bot) {
    throw new Error("Bot is not running");
  }
  await state.bot.stop();
  state.bot = null;
  state.token = null;
  console.log("[opencode-on-im] Telegram bot stopped");
}

export async function sendToAllBound(message: string): Promise<number> {
  const state = getState();
  if (!state.bot) {
    throw new Error("Bot is not running");
  }

  const chunks = splitMessage(message, 4000);
  let sent = 0;
  
  for (const binding of state.bindings.values()) {
    try {
        for (const chunk of chunks) {
          const msg = await state.bot.api.sendMessage(binding.telegramUserId, chunk);
          console.log(`[opencode-on-im] Sent to ${binding.telegramUserId} message_id=${msg.message_id}`);
        }
        sent++;
    } catch (error) {
      console.error(`[opencode-on-im] Failed to send to ${binding.telegramUserId}:`, error);
    }
  }
  return sent;
}

export async function sendToUser(userId: string, message: string): Promise<boolean> {
  const state = getState();
  if (!state.bot) {
    throw new Error("Bot is not running");
  }

  const chunks = splitMessage(message, 4000);

  try {
    for (const chunk of chunks) {
      const msg = await state.bot.api.sendMessage(userId, chunk);
      console.log(`[opencode-on-im] Sent to ${userId} message_id=${msg.message_id}`);
    }
    return true;
  } catch (error) {
    console.error(`[opencode-on-im] Failed to send to ${userId}:`, error);
    return false;
  }
}
