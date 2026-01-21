import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";

function bindingsPath(opencodeHome) {
  return path.join(opencodeHome, "opencode-on-im", "bindings.json");
}

test("bindings persistence: addBinding writes OPENCODE_HOME/opencode-on-im/bindings.json", async () => {
  const tmp = path.join(process.cwd(), ".tmp-test-opencode-home");
  fs.rmSync(tmp, { recursive: true, force: true });
  fs.mkdirSync(tmp, { recursive: true });

  const original = process.env.OPENCODE_HOME;
  process.env.OPENCODE_HOME = tmp;

  const m = await import("../dist/state.js?test=" + Date.now());
  const st = m.getState();

  for (const b of st.bindings.values()) {
    st.bindings.delete(b.telegramUserId);
  }

  m.addBinding("123", "alice");

  const p = bindingsPath(tmp);
  assert.ok(fs.existsSync(p));

  const raw = fs.readFileSync(p, "utf8");
  const parsed = JSON.parse(raw);
  assert.ok(Array.isArray(parsed.bindings));
  assert.equal(parsed.bindings.length, 1);
  assert.equal(parsed.bindings[0].telegramUserId, "123");
  assert.equal(parsed.bindings[0].telegramUsername, "alice");

  process.env.OPENCODE_HOME = original;
  fs.rmSync(tmp, { recursive: true, force: true });
});

test("bindings persistence: getState loads bindings from disk", async () => {
  const tmp = path.join(process.cwd(), ".tmp-test-opencode-home-2");
  fs.rmSync(tmp, { recursive: true, force: true });
  fs.mkdirSync(path.join(tmp, "opencode-on-im"), { recursive: true });

  const p = bindingsPath(tmp);
  fs.writeFileSync(
    p,
    JSON.stringify({ bindings: [{ telegramUserId: "456", telegramUsername: "bob", boundAt: 1 }] }, null, 2) + "\n",
    "utf8"
  );

  const original = process.env.OPENCODE_HOME;
  process.env.OPENCODE_HOME = tmp;

  const m = await import("../dist/state.js?test=" + Date.now());
  const st = m.getState();

  assert.ok(st.bindings.has("456"));
  assert.equal(st.bindings.get("456")?.telegramUsername, "bob");

  process.env.OPENCODE_HOME = original;
  fs.rmSync(tmp, { recursive: true, force: true });
});
