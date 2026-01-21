import { Bot } from "grammy";
import type { OpencodeClient } from "@opencode-ai/sdk";
import fs from "node:fs";
import path from "node:path";

export interface Binding {
  telegramUserId: string;
  telegramUsername?: string;
  boundAt: number;
}

export interface PendingCode {
  code: string;
  expiresAt: number;
}

export interface PendingResponse {
  sessionId: string;
  textBuffer: string;
  lastUpdate: number;
}

export interface PendingPermission {
  id: string;
  sessionID: string;
  title: string;
  type: string;
  pattern?: string | string[];
  time?: { created: number };
}

export interface SessionStatusState {
  sessionID: string;
  status: "busy" | "idle" | "retry";
  retry?: { attempt: number; message: string; next: number };
  updatedAt: number;
}

export interface TodoItem {
  id: string;
  content: string;
  status: string;
  priority: string;
}

export interface PluginState {
  bot: Bot | null;
  token: string | null;
  client: OpencodeClient | null;
  serverUrl: string | null;
  pendingCodes: Map<string, PendingCode>;
  bindings: Map<string, Binding>;
  activeSessionId: string | null;
  pendingResponses: Map<string, PendingResponse>;
  processedMessages: Set<string>;
  pendingPermissions: Map<string, PendingPermission>;
  sessionStatus: SessionStatusState | null;
  sessionTodos: Map<string, TodoItem[]>;
}

const state: PluginState = {
  bot: null,
  token: null,
  client: null,
  serverUrl: null,
  pendingCodes: new Map(),
  bindings: new Map(),
  activeSessionId: null,
  pendingResponses: new Map(),
  processedMessages: new Set(),
  pendingPermissions: new Map(),
  sessionStatus: null,
  sessionTodos: new Map(),
};

function getBindingsPersistPath(): string {
  const home = process.env.OPENCODE_HOME;
  if (home && home.length > 0) {
    return path.join(home, "opencode-on-im", "bindings.json");
  }
  return path.join(process.cwd(), ".opencode-on-im", "bindings.json");
}

function safeEnsureDirForFile(filePath: string): void {
  try {
    fs.mkdirSync(path.dirname(filePath), { recursive: true });
  } catch {
    return;
  }
}

function saveBindingsToDisk(): void {
  const filePath = getBindingsPersistPath();
  safeEnsureDirForFile(filePath);

  const bindings = Array.from(state.bindings.values());
  try {
    fs.writeFileSync(filePath, JSON.stringify({ bindings }, null, 2) + "\n", "utf8");
  } catch {
    return;
  }
}

function loadBindingsFromDisk(): void {
  const filePath = getBindingsPersistPath();
  try {
    const raw = fs.readFileSync(filePath, "utf8");
    const parsed = JSON.parse(raw) as { bindings?: Binding[] };

    if (Array.isArray(parsed.bindings)) {
      state.bindings.clear();
      for (const b of parsed.bindings) {
        if (!b || typeof b.telegramUserId !== "string") continue;
        state.bindings.set(b.telegramUserId, {
          telegramUserId: b.telegramUserId,
          telegramUsername: typeof b.telegramUsername === "string" ? b.telegramUsername : undefined,
          boundAt: typeof b.boundAt === "number" ? b.boundAt : Date.now(),
        });
      }
    }
  } catch {
    return;
  }
}

let didInit = false;

export function getState(): PluginState {
  if (!didInit) {
    didInit = true;
    loadBindingsFromDisk();
  }
  return state;
}

export function generateCode(): string {
  const chars = "abcdefghijklmnopqrstuvwxyz0123456789";
  let code = "";
  for (let i = 0; i < 10; i++) {
    code += chars[Math.floor(Math.random() * chars.length)];
  }
  return code;
}

export function createPendingCode(): string {
  const code = generateCode();
  const expiresAt = Date.now() + 60 * 1000;
  state.pendingCodes.set(code, { code, expiresAt });
  return code;
}

export function validateCode(code: string): boolean {
  const pending = state.pendingCodes.get(code);
  if (!pending) return false;
  if (Date.now() > pending.expiresAt) {
    state.pendingCodes.delete(code);
    return false;
  }
  state.pendingCodes.delete(code);
  return true;
}

export function addBinding(telegramUserId: string, telegramUsername?: string): void {
  state.bindings.set(telegramUserId, {
    telegramUserId,
    telegramUsername,
    boundAt: Date.now(),
  });
  saveBindingsToDisk();
}

export function removeBinding(telegramUserId: string): boolean {
  const removed = state.bindings.delete(telegramUserId);
  if (removed) {
    saveBindingsToDisk();
  }
  return removed;
}

export function getBindings(): Binding[] {
  return Array.from(state.bindings.values());
}

export function isUserBound(telegramUserId: string): boolean {
  return state.bindings.has(telegramUserId);
}
