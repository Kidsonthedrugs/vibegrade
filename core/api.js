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
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), 15000);
  try {
    const res = await fetch(BASE + path, {
      headers: { accept: "application/json" },
      credentials: "omit",
      signal: ctrl.signal,
    });
    if (!res.ok) throw new Error(`${res.status} ${path}`);
    const json = await res.json();
    cache.set(path, { t: Date.now(), v: json });
    return json;
  } catch (e) {
    if (e.name === "AbortError") throw new Error(`timeout ${path}`);
    throw e;
  } finally {
    clearTimeout(timer);
  }
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
  // The board mixes generations: v6 items carry `launch`, legacy v5 carry `token`.
  // V6 is the only generation our curve constants describe (800M / 4 ETH target).
  const kind = item.kind || (item.launch ? "v6" : "v5");
  const l = item.launch || item.token || item;
  const curve = l.curve || {};
  return {
    kind,
    token: l.tokenAddress,
    curve: l.curveAddress,
    name: l.name,
    symbol: l.symbol,
    image: l.content?.image?.uri || null,
    pairSymbol: l.pairSymbol,
    pairIsNative: l.pairIsNative,
    pairCurrencyAddress: l.pairCurrencyAddress || null,
    target: BigInt(l.targetPairUnits || 0),
    sold: BigInt(curve.tokensSoldGrossUnits || 0),
    pairPrincipal: BigInt(curve.pairReserveUnits || 0),
    taxBps: Number(l.taxBps || 0),
    lifecycle: l.lifecycle,
    graduated: !!l.graduated,
    createdAt: l.createdAt,
    createdAtBlock: l.createdBlock,
    market: l.market || (l.holderCount != null ? { holderCount: l.holderCount } : null),
    weights: l.weights || null,
    gifts: l.gifts || null,
    launcher: l.launcherAddress || l.creatorAddress,
    netPersonal: BigInt(l.initialNetPersonalUnits || 0),
  };
}

export async function candles(token, interval = "15m") {
  const j = await getJSON(
    `/api/v1/chains/${CHAIN_ID}/v6/launches/${encodeURIComponent(token)}/candles?interval=${interval}`
  );
  return (j.data && j.data.items) || [];
}

export const shortAddr = (a) => (a ? `${a.slice(0, 6)}…${a.slice(-4)}` : "?");

/** Launch detail + the market block (holders, volume) which only the board carries. */
export async function launchWithMarket(token) {
  const target = String(token).toLowerCase();
  const [detail, ...tabs] = await Promise.all([
    launch(token),
    ...TABS.map((t) => board(t).catch(() => [])),
  ]);
  const row = normalise({ kind: "v6", launch: detail.launch });
  for (const tab of tabs) {
    const hit = tab.map(normalise).find((r) => r.token && r.token.toLowerCase() === target);
    if (hit && hit.market) {
      row.market = hit.market;
      break;
    }
  }
  return row;
}

// IPFS gateway used by the app's own media route
export const mediaUrl = (cid, variant = "card.webp") =>
  cid ? `${BASE}/media/${cid.replace("ipfs://", "")}.${variant}` : null;
