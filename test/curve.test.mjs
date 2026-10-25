// Verification of core/curve.js against REAL on-chain quotes captured from
// Robinhood Chain Testnet (curve 0xb3bc6746dc4119b19f5887be42d4905c425b423b, token SWAG).
// Run: node test/curve.test.mjs
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, join } from "node:path";
import { quoteBuy, quoteSell, spotPrice, virtualToken, virtualPair } from "../core/curve.js";

const here = dirname(fileURLToPath(import.meta.url));
const jsonPath = process.env.RPC_JSON || join(here, "..", "..", "vibe-docs", "rpc_curve_math.json");
const raw = JSON.parse(readFileSync(jsonPath, "utf8"));

const words = (h) => {
  h = h.startsWith("0x") ? h.slice(2) : h;
  return Array.from({ length: h.length / 64 }, (_, i) => BigInt("0x" + h.slice(i * 64, i * 64 + 64)));
};
const get = (k) => words(raw[k]);

const state = {
  pairPrincipal: get("SWAG:pairPrincipal()")[0],
  sold: get("SWAG:sold()")[0],
  target: get("SWAG:targetPairUnits()")[0],
  taxBps: Number(get("SWAG:baseTaxBps()")[0]),
};

let pass = 0,
  fail = 0;
const rel = (a, b) => {
  const d = a > b ? a - b : b - a;
  return Number((d * 10n ** 18n) / (b === 0n ? 1n : b)) / 1e18;
};
function check(name, ok, detail) {
  if (ok) {
    pass++;
    console.log(`✅ ${name}${detail ? "  " + detail : ""}`);
  } else {
    fail++;
    console.log(`❌ ${name}  ${detail}`);
  }
}

console.log("state:", {
  pairPrincipal: state.pairPrincipal.toString(),
  sold: state.sold.toString(),
  target: state.target.toString(),
  taxBps: state.taxBps,
});
console.log("virtualToken =", virtualToken(state.target).toString(), " virtualPair =", virtualPair(state.target).toString());
console.log("");

for (const amt of ["0.001", "0.01", "0.1", "1.0"]) {
  const w = get(`SWAG:quoteBuy:${amt}`);
  const [grossOnChain, , costOnChain, feeOnChain] = w;
  const amountIn = BigInt(Math.round(Number(amt) * 1e6)) * 10n ** 12n; // 0.001 -> 1e15
  const q = quoteBuy({ amountIn, ...state });
  check(
    `buy ${amt}`,
    rel(q.tokens, grossOnChain) < 1e-15 && rel(q.cost, costOnChain) < 1e-15,
    `tokens off by ${rel(q.tokens, grossOnChain).toExponential(2)} | cost off by ${rel(q.cost, costOnChain).toExponential(2)} | fee model ${q.fee} vs chain ${feeOnChain}`
  );
}

{
  const w = get("SWAG:quoteSell:1000");
  const [netOnChain, proceedsOnChain, , pairOutOnChain] = w;
  const tokens = 1000n * 10n ** 18n;
  const q = quoteSell({ tokens, ...state });
  const abs = (a, b) => (a > b ? a - b : b - a);
  check(
    "sell 1000",
    abs(q.proceeds, proceedsOnChain) <= 2n && abs(q.pair, pairOutOnChain) <= 2n,
    `proceeds diff ${(q.proceeds - proceedsOnChain).toString()} wei | pairOut diff ${(q.pair - pairOutOnChain).toString()} wei (rounding)`
  );
}

{
  // graduation invariant: at P = target, sold must equal exactly 800M and price must be 4/200M
  const vt = virtualToken(state.target);
  const vp = virtualPair(state.target);
  const k = vt * vp;
  const remainingAtTarget = k / (vp + state.target);
  const soldAtGraduation = vt - remainingAtTarget;
  const want = 800n * 10n ** 6n * 10n ** 18n;
  const priceAtGrad = ((vp + state.target) * 10n ** 18n) / remainingAtTarget;
  const lpPrice = (state.target * 10n ** 18n) / (200n * 10n ** 6n * 10n ** 18n);
  check(
    "graduation invariant (sold = 800M)",
    rel(soldAtGraduation, want) < 1e-18,
    `sold at target = ${soldAtGraduation.toString()} (want ${want.toString()}, dust ${(soldAtGraduation - want).toString()})`
  );
  check("no price gap at graduation", priceAtGrad === lpPrice, `curve ${priceAtGrad} vs LP ${lpPrice}`);
}

console.log(`\n${pass} passed, ${fail} failed`);
process.exit(fail === 0 ? 0 : 1);
