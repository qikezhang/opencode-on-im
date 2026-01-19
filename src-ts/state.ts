import { Bot } from "grammy";
import type { OpencodeClient } from "@opencode-ai/sdk";

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

export interface PluginState {
  bot: Bot | null;
  token: string | null;
  client: OpencodeClient | null;
  pendingCodes: Map<string, PendingCode>;
  bindings: Map<string, Binding>;
  activeSessionId: string | null;
  pendingResponses: Map<string, PendingResponse>;
  processedMessages: Set<string>;
}

const state: PluginState = {
  bot: null,
  token: null,
  client: null,
  pendingCodes: new Map(),
  bindings: new Map(),
  activeSessionId: null,
  pendingResponses: new Map(),
  processedMessages: new Set(),
};

export function getState(): PluginState {
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
}

export function removeBinding(telegramUserId: string): boolean {
  return state.bindings.delete(telegramUserId);
}

export function getBindings(): Binding[] {
  return Array.from(state.bindings.values());
}

export function isUserBound(telegramUserId: string): boolean {
  return state.bindings.has(telegramUserId);
}
