import test from "node:test";
import assert from "node:assert/strict";

function parseApprove(text) {
  const args = text.split(/\s+/).slice(1);
  return { prefix: args[0], decision: args[1] };
}

test("approve command parsing", () => {
  assert.deepEqual(parseApprove("/approve abc123 once"), { prefix: "abc123", decision: "once" });
  assert.deepEqual(parseApprove("/approve 12345678 always"), { prefix: "12345678", decision: "always" });
  assert.deepEqual(parseApprove("/approve deadbeef reject"), { prefix: "deadbeef", decision: "reject" });
});
