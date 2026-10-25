// Thin client for the vibe/vibe testnet API (undocumented; discovered by inspection).
// Works in the browser (Vercel) directly. For local Node scripts behind the
// Nekoray proxy, use bot/*.py instead (urllib honours the proxy explicitly).

export const CHAIN_ID = 46630;
// Same-origin: /api and /media are proxied to the app by vercel.json (prod)
// and by scripts/serve.mjs (local). Avoids CORS and country-level blocking.
const BASE = "";
const TTL = 30_000;

const cache = new Map();
async function getJSON(path) {
  const hit = cache.get(path);
  if (hit && Date.now() - hit.t < TTL) return hit.v;
  const res = await fetch(BASE + path, {
    headers: { accept: "application/json" },
    credentials: "omit",
  });
  if (!res.ok) throw new Error(`${res.status} ${path}`);
  const json = await res.json();
  cache.set(path, { t: Date.now(), v: json });
  return json;
}

export const TABS = ["TRENDING", "NEW", "FINAL_STRETCH", "GRADUATED", "MOVERS"];

export async function board(tab = "FINAL_STRETCH") {
  const j = await getJSON(`/api/v1/chains/${CHAIN_ID}/board?tab=${tab}`);
  return j.data.items || [];
}

export async function launch(token) {
  const j = await getJSON(`/api/v1/chains/${CHAIN_ID}/v6/launches/${encodeURIComponent(token)}`);
  return j.data;
}

export async function config() {
  const j = await getJSON(`/api/v1/chains/${CHAIN_ID}/config`);
  return j.data;
}

export async function ethUsd() {
  const j = await getJSON(`/api/v1/chains/${CHAIN_ID}/market/eth-usd`);
  return Number(j.data.usdPerEthCents) / 100;
}

/** Normalise a board item into the numbers the radar needs (all base units as BigInt). */
export function normalise(item) {
  const l = item.launch || item;
  return {
    token: l.tokenAddress,
    curve: l.curveAddress,
    name: l.name,
    symbol: l.symbol,
    image: l.content?.image?.uri || null,
    pairSymbol: l.pairSymbol,
    pairIsNative: l.pairIsNative,
    target: BigInt(l.targetPairUnits || 0),
    sold: BigInt(l.curve?.tokensSoldGrossUnits || 0),
    pairPrincipal: BigInt(l.curve?.pairReserveUnits || 0),
    taxBps: Number(l.taxBps || 0),
    lifecycle: l.lifecycle,
    graduated: !!l.graduated,
    createdAt: l.createdAt,
    createdAtBlock: l.createdBlock,
    market: l.market || null,
    weights: l.weights || null,
    gifts: l.gifts || null,
    launcher: l.launcherAddress,
  };
}

// IPFS gateway used by the app's own media route
export const mediaUrl = (cid, variant = "card.webp") =>
  cid ? `${BASE}/media/${cid.replace("ipfs://", "")}.${variant}` : null;
