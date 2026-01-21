import { Bot } from "grammy";
import {
  getState,
  validateCode,
  addBinding,
  isUserBound,
} from "../state.js";

function isPrivateChat(ctx: { chat?: { type?: string } }): boolean {
  return ctx.chat?.type === "private";
}

function formatSessionShort(id: string | null): string {
  if (!id) return "none";
  return `${id.slice(0, 8)}...`;
}

async function ensureActiveSession(): Promise<string | null> {
  const state = getState();
  if (!state.client) return null;

  if (!state.activeSessionId) {
    const res = await state.client.session.create({});
    if (res.data?.id) {
      state.activeSessionId = res.data.id;
    }
  }

  return state.activeSessionId;
}

function resolvePermissionId(prefixOrId: string): string | null {
  const state = getState();
  if (state.pendingPermissions.has(prefixOrId)) return prefixOrId;

  const normalized = prefixOrId.toLowerCase();
  for (const id of state.pendingPermissions.keys()) {
    if (id.toLowerCase().startsWith(normalized)) return id;
  }

  return null;
}

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
    if (!isPrivateChat(ctx)) {
      return;
    }

    const userId = String(ctx.from?.id);
    if (isUserBound(userId)) {
      await ctx.reply("You are already bound. Send a message to chat with AI.");
      return;
    }
    await ctx.reply("Welcome! Please enter your 10-character verification code to bind.");
  });

  bot.command("help", async (ctx) => {
    if (!isPrivateChat(ctx)) {
      return;
    }

    await ctx.reply(
      [
        "OpenCode on IM commands:",
        "- /start: begin binding flow",
        "- /status: show OpenCode + session status",
        "- /web: get web interface URL",
        "- /session list: list sessions",
        "- /session use <n|sessionId>: switch active session",
        "- /session new: create a new session",
        "- /approve <permissionId> once|always|reject: reply to permission request",
        "- /agent cycle: cycle agent",
        "- /interrupt: interrupt current session",
        "- /prompt clear: clear TUI prompt",
        "- /prompt submit: submit TUI prompt",
        "- /page up|down|half-up|half-down|first|last: scroll session view",
        "",
        "Any normal text message will be sent to OpenCode as a prompt.",
      ].join("\n")
    );
  });

  bot.command("status", async (ctx) => {
    if (!isPrivateChat(ctx)) {
      return;
    }

    const userId = String(ctx.from?.id);
    if (!isUserBound(userId)) {
      await ctx.reply("You are not bound. Use /start to begin.");
      return;
    }

    const connected = state.client ? "✅ Connected" : "❌ Not connected";
    const sessionShort = formatSessionShort(state.activeSessionId);

    const status = state.sessionStatus
      ? state.sessionStatus.status === "retry" && state.sessionStatus.retry
        ? `retry (attempt=${state.sessionStatus.retry.attempt}, next=${Math.round(state.sessionStatus.retry.next / 1000)}s)`
        : state.sessionStatus.status
      : "unknown";

    const todos = state.activeSessionId ? state.sessionTodos.get(state.activeSessionId) : undefined;
    const todoLine = todos && todos.length > 0
      ? `${todos.filter((t) => t.status === "completed").length}/${todos.length}`
      : "none";

    const pendingPermCount = state.pendingPermissions.size;

    await ctx.reply(
      [
        connected,
        `Active session: ${sessionShort}`,
        `Status: ${status}`,
        `Todos: ${todoLine}`,
        `Pending permissions: ${pendingPermCount}`,
      ].join("\n")
    );
  });

  bot.command("session", async (ctx) => {
    if (!isPrivateChat(ctx)) {
      return;
    }

    const userId = String(ctx.from?.id);
    if (!isUserBound(userId)) {
      await ctx.reply("You are not bound. Use /start to begin.");
      return;
    }

    const text = ctx.message?.text || "";
    const args = text.split(/\s+/).slice(1);
    const sub = args[0];

    if (!state.client) {
      await ctx.reply("❌ Not connected to OpenCode.");
      return;
    }

    if (sub === "list") {
      try {
        const res = await state.client.session.list({});
        const sessions = res.data || [];
        if (sessions.length === 0) {
          await ctx.reply("No sessions.");
          return;
        }

        const lines = sessions.map((s, i) => {
          const marker = s.id === state.activeSessionId ? "*" : " ";
          const title = s.title ? s.title : "(untitled)";
          return `${marker}${i + 1}. ${title} (${s.id.slice(0, 8)}...)`;
        });

        await ctx.reply(lines.join("\n"));
      } catch (err) {
        await ctx.reply(`Error: ${err instanceof Error ? err.message : "Unknown error"}`);
      }
      return;
    }

    if (sub === "use") {
      const target = args[1];
      if (!target) {
        await ctx.reply("Usage: /session use <n|sessionId>");
        return;
      }

      try {
        const res = await state.client.session.list({});
        const sessions = res.data || [];

        if (sessions.length === 0) {
          await ctx.reply("No sessions available.");
          return;
        }

        let id: string | undefined;
        const n = Number(target);
        if (Number.isFinite(n)) {
          if (n >= 1 && n <= sessions.length) {
            id = sessions[n - 1]?.id;
          } else {
            await ctx.reply(`Invalid session number. Use 1-${sessions.length}.`);
            return;
          }
        } else {
          const normalized = target.toLowerCase();
          id = sessions.find((s) => s.id.toLowerCase() === normalized || s.id.toLowerCase().startsWith(normalized))?.id;
        }

        if (!id) {
          await ctx.reply("Session not found.");
          return;
        }

        state.activeSessionId = id;
        await ctx.reply(`Switched active session to ${formatSessionShort(id)} (global)`);
      } catch (err) {
        await ctx.reply(`Error: ${err instanceof Error ? err.message : "Unknown error"}`);
      }
      return;
    }

    if (sub === "new") {
      try {
        const res = await state.client.session.create({});
        if (res.data?.id) {
          state.activeSessionId = res.data.id;
          await ctx.reply(`✅ Created new session: ${formatSessionShort(res.data.id)}`);
        } else {
          await ctx.reply("Failed to create session.");
        }
      } catch (err) {
        await ctx.reply(`Error: ${err instanceof Error ? err.message : "Unknown error"}`);
      }
      return;
    }

    await ctx.reply("Usage: /session list | /session use <n|sessionId> | /session new");
  });

  bot.command("approve", async (ctx) => {
    if (!isPrivateChat(ctx)) {
      return;
    }

    const userId = String(ctx.from?.id);
    if (!isUserBound(userId)) {
      await ctx.reply("You are not bound. Use /start to begin.");
      return;
    }

    const text = ctx.message?.text || "";
    const args = text.split(/\s+/).slice(1);
    const prefix = args[0];
    const decision = args[1];

    if (!prefix || !decision) {
      await ctx.reply("Usage: /approve <permissionId> once|always|reject");
      return;
    }

    const permissionId = resolvePermissionId(prefix);
    if (!permissionId) {
      await ctx.reply("Permission not found. Use /status to see pending permissions.");
      return;
    }

    const perm = state.pendingPermissions.get(permissionId);
    const sessionId = perm?.sessionID || (await ensureActiveSession());

    if (!state.client || !sessionId) {
      await ctx.reply("❌ Not connected to OpenCode.");
      return;
    }

    if (decision !== "once" && decision !== "always" && decision !== "reject") {
      await ctx.reply("Usage: /approve <permissionId> once|always|reject");
      return;
    }

    try {
      const res = await state.client.postSessionIdPermissionsPermissionId({
        path: { id: sessionId, permissionID: permissionId },
        body: { response: decision },
      });

      if (res.data) {
        state.pendingPermissions.delete(permissionId);
        await ctx.reply(`Approved (${decision}) for ${permissionId.slice(0, 8)}...`);
      } else {
        await ctx.reply("Failed to approve permission.");
      }
    } catch (err) {
      await ctx.reply(`Error: ${err instanceof Error ? err.message : "Unknown error"}`);
    }
  });

  bot.command("agent", async (ctx) => {
    if (!isPrivateChat(ctx)) {
      return;
    }

    const userId = String(ctx.from?.id);
    if (!isUserBound(userId)) {
      await ctx.reply("You are not bound. Use /start to begin.");
      return;
    }

    const text = ctx.message?.text || "";
    const args = text.split(/\s+/).slice(1);
    const sub = args[0];

    if (!state.client) {
      await ctx.reply("❌ Not connected to OpenCode.");
      return;
    }

    if (sub === "cycle") {
      try {
        const res = await state.client.tui.executeCommand({ body: { command: "agent.cycle" } });
        await ctx.reply(res.data ? "Agent cycled." : "Failed to cycle agent.");
      } catch (err) {
        await ctx.reply(`Error: ${err instanceof Error ? err.message : "Unknown error"}`);
      }
      return;
    }

    await ctx.reply("Usage: /agent cycle");
  });

  bot.command("interrupt", async (ctx) => {
    if (!isPrivateChat(ctx)) {
      return;
    }

    const userId = String(ctx.from?.id);
    if (!isUserBound(userId)) {
      await ctx.reply("You are not bound. Use /start to begin.");
      return;
    }

    if (!state.client) {
      await ctx.reply("❌ Not connected to OpenCode.");
      return;
    }

    try {
      const res = await state.client.tui.executeCommand({ body: { command: "session.interrupt" } });
      await ctx.reply(res.data ? "Interrupt requested." : "Failed to interrupt.");
    } catch (err) {
      await ctx.reply(`Error: ${err instanceof Error ? err.message : "Unknown error"}`);
    }
  });

  bot.command("prompt", async (ctx) => {
    if (!isPrivateChat(ctx)) {
      return;
    }

    const userId = String(ctx.from?.id);
    if (!isUserBound(userId)) {
      await ctx.reply("You are not bound. Use /start to begin.");
      return;
    }

    const text = ctx.message?.text || "";
    const args = text.split(/\s+/).slice(1);
    const sub = args[0];

    if (!state.client) {
      await ctx.reply("❌ Not connected to OpenCode.");
      return;
    }

    if (sub === "clear") {
      try {
        const res = await state.client.tui.executeCommand({ body: { command: "prompt.clear" } });
        await ctx.reply(res.data ? "Prompt cleared." : "Failed to clear prompt.");
      } catch (err) {
        await ctx.reply(`Error: ${err instanceof Error ? err.message : "Unknown error"}`);
      }
      return;
    }

    if (sub === "submit") {
      try {
        const res = await state.client.tui.executeCommand({ body: { command: "prompt.submit" } });
        await ctx.reply(res.data ? "Prompt submitted." : "Failed to submit prompt.");
      } catch (err) {
        await ctx.reply(`Error: ${err instanceof Error ? err.message : "Unknown error"}`);
      }
      return;
    }

    await ctx.reply("Usage: /prompt clear | /prompt submit");
  });

  bot.command("page", async (ctx) => {
    if (!isPrivateChat(ctx)) {
      return;
    }

    const userId = String(ctx.from?.id);
    if (!isUserBound(userId)) {
      await ctx.reply("You are not bound. Use /start to begin.");
      return;
    }

    const text = ctx.message?.text || "";
    const args = text.split(/\s+/).slice(1);
    const sub = args[0];

    if (!state.client) {
      await ctx.reply("❌ Not connected to OpenCode.");
      return;
    }

    const map: Record<string, string> = {
      up: "session.page.up",
      down: "session.page.down",
      "half-up": "session.half.page.up",
      "half-down": "session.half.page.down",
      first: "session.first",
      last: "session.last",
    };

    const cmd = sub ? map[sub] : undefined;
    if (!cmd) {
      await ctx.reply("Usage: /page up|down|half-up|half-down|first|last");
      return;
    }

    try {
      const res = await state.client.tui.executeCommand({ body: { command: cmd } });
      await ctx.reply(res.data ? `OK: ${sub}` : `Failed: ${sub}`);
    } catch (err) {
      await ctx.reply(`Error: ${err instanceof Error ? err.message : "Unknown error"}`);
    }
  });

  bot.command("web", async (ctx) => {
    if (!isPrivateChat(ctx)) {
      return;
    }

    const userId = String(ctx.from?.id);
    if (!isUserBound(userId)) {
      await ctx.reply("You are not bound. Use /start to begin.");
      return;
    }

    if (!state.serverUrl) {
      await ctx.reply("❌ Server URL not available.");
      return;
    }

    await ctx.reply(`🌐 Web interface: ${state.serverUrl}`);
  });

  bot.on("message:text", async (ctx) => {
    if (!isPrivateChat(ctx)) {
      return;
    }

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
