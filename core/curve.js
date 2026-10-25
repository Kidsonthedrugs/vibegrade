// VibeGrade — shared bonding-curve math for vibe/vibe V6 launches (Robinhood Chain 46630)
// Reverse-engineered and verified against on-chain quoteBuyExactIn / quoteSell (0% error).
// All values are BigInt base units unless stated otherwise.

export const WAD = 10n ** 18n;
export const BPS = 10_000n;

// Protocol constants, confirmed live from curve 0xb3bc6746... and factory target 4e18.
export const CURVE_SUPPLY = 800n * 10n ** 6n * WAD; // 800M sold on the curve
export const LP_SUPPLY = 200n * 10n ** 6n * WAD; // 200M into the v4 pool
export const TOTAL_SUPPLY = 1_000n * 10n ** 6n * WAD; // 1B

// virtual token reserve = 800M * 4/3 ; virtual pair reserve = target / 3
export const virtualToken = (target) => (CURVE_SUPPLY * 4n) / 3n;
export const virtualPair = (target) => target / 3n;

/** fee-on-top split: cost = in * 10000 / (10000 + taxBps) */
export function splitFee(amountIn, taxBps) {
  const cost = (amountIn * BPS) / (BPS + BigInt(taxBps));
  return { cost, fee: amountIn - cost };
}

/** exact tokens received for `amountIn` gross pair units (fee applied first) */
export function quoteBuy({ amountIn, sold, pairPrincipal, target, taxBps }) {
  const { cost, fee } = splitFee(amountIn, taxBps);
  const vt = virtualToken(target);
  const vp = virtualPair(target);
  const k = vt * vp;
  const remaining = vt - sold;
  const out = remaining - k / (vp + pairPrincipal + cost);
  return { tokens: out, cost, fee };
}

/** exact pair received for `tokens` (gross), net of fee.
 *  NOTE: sells deduct taxBps straight off the proceeds (proceeds * tax / 10000),
 *  while buys use the fee-on-top division. Verified on-chain to 1 wei. */
export function quoteSell({ tokens, sold, pairPrincipal, target, taxBps }) {
  const vt = virtualToken(target);
  const vp = virtualPair(target);
  const denom = vt - sold + tokens;
  const proceeds = ((vp + pairPrincipal) * tokens) / denom;
  const fee = (proceeds * BigInt(taxBps)) / BPS;
  return { pair: proceeds - fee, proceeds, fee };
}

/** spot price in pair units per token (WAD-scaled) */
export function spotPrice({ sold, pairPrincipal, target }) {
  const vt = virtualToken(target);
  const vp = virtualPair(target);
  return ((vp + pairPrincipal) * WAD) / (vt - sold);
}

/** how much pair input is still needed to complete the curve (net of fee) */
export function pairToGraduation({ pairPrincipal, target }) {
  return target > pairPrincipal ? target - pairPrincipal : 0n;
}

/** progress in bps toward graduation */
export function progressBps({ pairPrincipal, target }) {
  if (target === 0n) return 0;
  return Number((pairPrincipal * BPS) / target);
}

/** small helper: pair input (net) needed to reach a specific sold amount */
export function pairToReachSold({ sold, pairPrincipal, target, wantSold }) {
  const vt = virtualToken(target);
  const vp = virtualPair(target);
  const k = vt * vp;
  const remainingAfter = vt - wantSold;
  if (remainingAfter <= 0n) return null;
  const vpAfter = k / remainingAfter;
  const need = vpAfter - vp - pairPrincipal;
  return need > 0n ? need : 0n;
}

// ---- formatting helpers (UI) ----
export function fmtEth(wei, digits = 4) {
  const whole = wei / WAD;
  const frac = (wei % WAD).toString().padStart(18, "0").slice(0, digits);
  const s = `${whole}.${frac}`.replace(/\.?0+$/, "");
  return s === "" ? "0" : s;
}

export function fmtTokens(base, digits = 0) {
  const n = Number(base / WAD);
  if (!Number.isFinite(n)) return "0";
  if (n >= 1e9) return (n / 1e9).toFixed(2) + "B";
  if (n >= 1e6) return (n / 1e6).toFixed(2) + "M";
  if (n >= 1e3) return (n / 1e3).toFixed(1) + "K";
  return n.toFixed(digits);
}
