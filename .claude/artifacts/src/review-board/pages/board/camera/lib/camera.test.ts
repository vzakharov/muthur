import assert from "node:assert/strict";
import { describe, it } from "node:test";

import { centred, fitTo, toWorld, union, zoomAt } from "./camera.ts";

describe("zoomAt", () => {
  it("keeps the world point under the anchor in place", () => {
    const camera = { x: 10, y: -20, zoom: 0.5 };
    const anchor = { x: 300, y: 200 };
    const before = toWorld(camera, anchor);
    const after = toWorld(zoomAt(camera, anchor, 1.7), anchor);
    assert.ok(Math.abs(before.x - after.x) < 1e-9);
    assert.ok(Math.abs(before.y - after.y) < 1e-9);
  });
});

describe("fitTo", () => {
  it("centres the bounds in the viewport", () => {
    const camera = fitTo(
      { x: 100, y: 100, width: 2000, height: 1000 },
      { x: 0, y: 0, width: 1096, height: 1000 },
    );
    assert.equal(camera.zoom, 0.5);
    const centre = toWorld(camera, { x: 548, y: 500 });
    assert.deepEqual(centre, { x: 1100, y: 600 });
  });
});

describe("union", () => {
  it("spans every rectangle, and nothing for none", () => {
    assert.deepEqual(
      union([
        { x: 0, y: 0, width: 10, height: 10 },
        { x: -5, y: 5, width: 10, height: 20 },
      ]),
      { x: -5, y: 0, width: 15, height: 25 },
    );
    assert.equal(union([]), undefined);
  });
});

describe("centred", () => {
  it("puts the world point at the screen point without changing zoom", () => {
    const camera = centred(
      { x: 0, y: 0, zoom: 2 },
      { x: 100, y: 50 },
      { x: 400, y: 300 },
    );
    assert.equal(camera.zoom, 2);
    assert.deepEqual(toWorld(camera, { x: 400, y: 300 }), { x: 100, y: 50 });
  });
});
