import { startBot, sendToAllBound } from "./telegram/bot.js";
import { createPendingCode, getBindings, getState } from "./state.js";
import { createOpencodeClient } from "@opencode-ai/sdk";

const token = process.env.TELEGRAM_TOKEN;
if (!token) {
  console.error("[opencode-on-im] TELEGRAM_TOKEN not set");
  process.exit(1);
}

const OPENCODE_URL = process.env.OPENCODE_URL || "http://127.0.0.1:4096";

console.log("[opencode-on-im] Starting Telegram bot in standalone mode...");
console.log(`[opencode-on-im] Connecting to OpenCode at ${OPENCODE_URL}`);

interface PendingResponse {
  sessionId: string;
  textBuffer: string;
  lastUpdate: number;
}

const pendingResponses = new Map<string, PendingResponse>();
const processedMessages = new Set<string>();

async function handleEvent(event: { type: string; properties?: Record<string, unknown> }) {
  const state = getState();
  
  if (event.type === "session.created") {
    const info = event.properties?.info as { id?: string } | undefined;
    if (info?.id) {
      state.activeSessionId = info.id;
      console.log(`[opencode-on-im] Session created: ${info.id}`);
    }
  }

  if (event.type === "message.part.updated" && state.bot && state.bindings.size > 0) {
    const part = event.properties?.part as { 
      type: string; 
      sessionID?: string; 
      messageID?: string; 
      text?: string;
      tool?: string;
      state?: { type: string; output?: string };
    } | undefined;
    
    if (part?.type === "text" && part.sessionID && part.messageID) {
      const key = `${part.sessionID}:${part.messageID}`;
      
      if (!pendingResponses.has(key)) {
        pendingResponses.set(key, {
          sessionId: part.sessionID,
          textBuffer: "",
          lastUpdate: Date.now(),
        });
      }
      
      const pending = pendingResponses.get(key)!;
      const delta = event.properties?.delta as string | undefined;
      if (delta) {
        pending.textBuffer += delta;
      } else if (part.text) {
        pending.textBuffer = part.text;
      }
      pending.lastUpdate = Date.now();
    }
    
    if (part?.type === "tool" && part.state?.type === "completed" && part.state.output) {
      const output = part.state.output;
      if (output.length > 100) {
        const summary = output.length > 1000 ? output.slice(0, 1000) + "..." : output;
        try {
          await sendToAllBound(`[Tool: ${part.tool}]\n${summary}`);
        } catch {}
      }
    }
  }

  if (event.type === "session.idle" && state.bot && state.bindings.size > 0) {
    const sessionId = event.properties?.sessionID as string | undefined;
    
    for (const [key, pending] of pendingResponses.entries()) {
      if (pending.sessionId === sessionId && pending.textBuffer.length > 0) {
        if (!processedMessages.has(key)) {
          processedMessages.add(key);
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
        pendingResponses.delete(key);
      }
    }

    if (processedMessages.size > 100) {
      const arr = Array.from(processedMessages);
      arr.slice(0, 50).forEach((k) => processedMessages.delete(k));
    }
  }

  if (event.type === "command.executed" && state.bot && state.bindings.size > 0) {
    const name = event.properties?.name as string | undefined;
    const args = event.properties?.arguments as string | undefined;
    try {
      await sendToAllBound(`[Command] ${name} ${args || ""}`);
    } catch {}
  }
}

async function subscribeToEvents(client: ReturnType<typeof createOpencodeClient>) {
  console.log("[opencode-on-im] Subscribing to OpenCode events...");
  
  try {
    const result = await client.global.event({});
    const stream = result.stream;

    console.log("[opencode-on-im] Event subscription active");

    for await (const globalEvent of stream) {
      if (globalEvent) {
        try {
          const payload = (globalEvent as { directory: string; payload: { type: string; properties?: Record<string, unknown> } }).payload;
          await handleEvent(payload);
        } catch (err) {
          console.error("[opencode-on-im] Error handling event:", err);
        }
      }
    }
  } catch (err) {
    console.error("[opencode-on-im] Event subscription error:", err);
    setTimeout(() => subscribeToEvents(client), 5000);
  }
}

async function main(botToken: string) {
  try {
    const state = getState();
    
    const client = createOpencodeClient({
      baseUrl: OPENCODE_URL,
    });
    state.client = client;
    console.log("[opencode-on-im] OpenCode client created");

    const sessionsRes = await client.session.list({});
    if (sessionsRes.data && sessionsRes.data.length > 0) {
      state.activeSessionId = sessionsRes.data[0].id;
      console.log(`[opencode-on-im] Using session: ${state.activeSessionId}`);
    } else {
      const newSession = await client.session.create({});
      if (newSession.data) {
        state.activeSessionId = newSession.data.id;
        console.log(`[opencode-on-im] Created new session: ${state.activeSessionId}`);
      }
    }

    subscribeToEvents(client);

    await startBot(botToken);
    console.log("[opencode-on-im] Bot is running. Press Ctrl+C to stop.");
    
    if (process.argv.includes("--test")) {
      console.log("\n=== TEST MODE ===");
      const code = createPendingCode();
      console.log(`Verification code: ${code}`);
      console.log("Send this code to the bot to bind, then send a message.\n");
      
      const checkBinding = setInterval(() => {
        const bindings = getBindings();
        if (bindings.length > 0) {
          console.log("User bound:", bindings[0].telegramUsername || bindings[0].telegramUserId);
          clearInterval(checkBinding);
          
          sendToAllBound("You are connected! Send a message to chat with AI.")
            .then(() => console.log("Sent welcome message"));
        }
      }, 1000);
    }
    
    await new Promise(() => {});
  } catch (err) {
    console.error("[opencode-on-im] Failed to start:", err);
    process.exit(1);
  }
}

main(token);

process.on("SIGINT", () => {
  console.log("\n[opencode-on-im] Shutting down...");
  process.exit(0);
});

process.on("SIGTERM", () => {
  console.log("\n[opencode-on-im] Shutting down...");
  process.exit(0);
});
