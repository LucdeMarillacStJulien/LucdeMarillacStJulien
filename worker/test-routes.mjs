// node worker/test-routes.mjs
import assert from "node:assert/strict";
import { upstreamFor } from "./index.js";

assert.match(upstreamFor("/stats.svg"), /\/main\/assets\/stats\.svg$/);
assert.match(upstreamFor("/snake-dark.svg"), /\/output\/snake-dark\.svg$/);
assert.equal(upstreamFor("/stats.svg"), upstreamFor("stats.svg"));
assert.equal(upstreamFor("/"), null);
assert.equal(upstreamFor("/../assets/stats.svg"), null);
assert.equal(upstreamFor("/unknown.svg"), null);

console.log("routes ok");
