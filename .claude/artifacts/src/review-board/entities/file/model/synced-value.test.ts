import assert from "node:assert/strict";
import { test } from "node:test";
import { synced } from "./synced-value.ts";

interface Gate {
  release(): void;
  promise: Promise<void>;
}
function gate(): Gate {
  let release: () => void = () => undefined;
  const promise = new Promise<void>((resolve) => {
    release = resolve;
  });
  return { release, promise };
}

function make() {
  const writes: string[] = [];
  const gates: Gate[] = [];
  const failures: unknown[] = [];
  let changes = 0;
  const value = synced<string>({
    initial: "",
    equals: (a, b) => a === b,
    write: async (next) => {
      writes.push(next);
      const g = gate();
      gates.push(g);
      await g.promise;
    },
    changed: () => changes++,
    failed: (error) => failures.push(error),
  });
  return { value, writes, gates, failures, changes: () => changes };
}

const tick = () => new Promise<void>((resolve) => setImmediate(resolve));

test("an unchanged value writes nothing", async () => {
  const { value, writes } = make();
  value.set("", "t1");
  await tick();
  assert.deepEqual(writes, []);
});

test("one write is in flight at a time and the latest change is the one queued", async () => {
  const { value, writes, gates } = make();
  value.set("a", "t1");
  value.set("b", "t2");
  value.set("c", "t3");
  await tick();
  assert.deepEqual(writes, ["a"]);
  gates[0]?.release();
  await tick();
  assert.deepEqual(writes, ["a", "c"]);
  gates[1]?.release();
  await tick();
  assert.deepEqual(writes, ["a", "c"]);
  assert.equal(value.get(), "c");
  assert.equal(value.at(), "t3");
});

test("a remote value is ignored while a local change is unwritten, taken after", async () => {
  const { value, gates } = make();
  value.set("mine", "t1");
  value.receive({ value: "theirs", at: "t0" });
  assert.equal(value.get(), "mine");
  gates[0]?.release();
  await tick();
  value.receive({ value: "theirs", at: "t2" });
  assert.equal(value.get(), "theirs");
  assert.equal(value.at(), "t2");
});

test("a missing remote document restores the initial value", () => {
  const { value } = make();
  value.receive({ value: "x", at: "t1" });
  value.receive(null);
  assert.equal(value.get(), "");
  assert.equal(value.at(), "");
});

test("a failed write is reported and drops what was queued", async () => {
  const failures: unknown[] = [];
  const value = synced<string>({
    initial: "",
    equals: (a, b) => a === b,
    write: () => Promise.reject(new Error("denied")),
    changed: () => undefined,
    failed: (error) => failures.push(error),
  });
  value.set("a", "t1");
  await tick();
  assert.equal(failures.length, 1);
  assert.equal(value.get(), "a");
});
