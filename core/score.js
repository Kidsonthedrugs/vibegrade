// Launch Score — browser port of bot/score.py. Same rubric, same numbers.
// Each component is a documented rule; the score is advice, not a promise.

export const SCORE_WEIGHTS = {
  "tax fit": 20,
  weights: 25,
  airdrop: 20,
  pair: 10,
  "opening buy": 15,
  distribution: 10,
};

const clamp = (v) => Math.max(0, Math.min(100, v));

function taxPoints(taxBps) {
  const table = {
    100: [85, "1% keeps the most value in every buy — fastest route to graduation, thin creator revenue."],
    200: [100, "2% is the balanced tier: sells stay cheap and the project share still funds a treasury."],
    300: [70, "3% is the most extractive tier; buyers feel it on every trade and graduation slows."],
  };
  return table[taxBps] || [40, `${(taxBps / 100).toFixed(2)}% is outside the 1/2/3% tiers buyers expect.`];
}

function weightsPoints(w = {}) {
  const cash = Number(w.cashBps || 0);
  const holders = Number(w.holdersBps || 0);
  const burn = Number(w.burnBps || 0);
  const holdersPair = Number(w.holdersPairBps || 0);
  const total = cash + holders + burn + holdersPair;
  if (total === 0) return [0, "No project share is routed anywhere — the 80% has nowhere to go."];
  const community = holders + holdersPair;
  let score = Math.min(60, (community / 10000) * 80);
  score += cash / 10000 >= 0.05 && cash / 10000 <= 0.5 ? 25 : 10;
  score += burn <= 2000 ? 15 : 5;
  let note;
  if (cash === 10000) {
    score = 35;
    note = "100% to the treasury: nothing rewards holders, so there is no reason to hold.";
  } else if (community >= 4000) {
    note = `${(community / 100).toFixed(0)}% to holders, ${(cash / 100).toFixed(0)}% to treasury, ${(burn / 100).toFixed(0)}% burned.`;
  } else {
    note = `Only ${(community / 100).toFixed(0)}% reaches holders — the token has no holder incentive.`;
  }
  return [clamp(score), note];
}

function airdropPoints(gifts = {}) {
  const count = Number(gifts.count || 0);
  const reserved = Number(gifts.reservedUnits || 0) / 1e18;
  if (!count || !reserved) {
    return [
      0,
      "No graduation airdrop configured. This is the single biggest lever: it is what turns strangers into holders the moment the curve completes.",
    ];
  }
  const pct = (reserved / 1e9) * 100;
  return [
    clamp(Math.min(100, 40 + pct * 12)),
    `Airdrop reserved for ${count.toLocaleString()} wallets (~${pct.toFixed(1)}% of supply) — distribution is designed in.`,
  ];
}

function pairPoints(r) {
  return r.pairIsNative
    ? [100, "Paired against ETH: deepest liquidity and no second tax on every trade."]
    : [
        55,
        `Paired against ${r.pairSymbol || "a token"}: every trade also pays that token's own tax, so buyers pay twice.`,
      ];
}

function openingPoints(r) {
  const net = Number(r.netPersonal || 0);
  const share = (net / 1e27) * 100;
  if (!net) {
    return [
      30,
      "No opening buy: the creator holds nothing, and buyers read that as low conviction. A small buy at creation is the cheapest signal you can send.",
    ];
  }
  if (share < 0.5) return [100, `Opening buy is ${share.toFixed(2)}% of supply — skin in the game without cornering the float.`];
  if (share <= 10) return [80, `Opening buy is ${share.toFixed(2)}% of supply — fine, watch the concentration.`];
  return [
    45,
    `Opening buy is ${share.toFixed(1)}% of supply — that much in one wallet scares off the second buyer, and it eats the 50% budget that could have gone to an airdrop.`,
  ];
}

function distributionPoints(r) {
  const holders = Number((r.market || {}).holderCount || 0);
  if (!holders) return [55, "No holder data yet — neutral."];
  if (holders >= 500) return [100, `${holders.toLocaleString()} holders — healthy, organic-looking distribution.`];
  if (holders >= 100) return [85, `${holders.toLocaleString()} holders — solid base.`];
  if (holders >= 30) return [60, `${holders.toLocaleString()} holders — early, needs a distribution push.`];
  return [30, `Only ${holders} holders — the curve is being filled by very few wallets.`];
}

export function etaText(r) {
  const vol = Number((r.market || {}).volume24hPairUnits || 0);
  const need = Number(r.target || 0) - Number(r.pairPrincipal || 0);
  if (vol <= 0 || need <= 0) return "—";
  const minutes = need / 1e18 / (vol / 1e18 / 1440);
  if (minutes < 60) return `~${minutes.toFixed(0)} min at the current 24h pace`;
  if (minutes < 6000) return `~${(minutes / 60).toFixed(1)} h at the current 24h pace`;
  return `~${(minutes / 1440).toFixed(1)} days at the current 24h pace`;
}

export function scoreLaunch(r) {
  const parts = {
    "tax fit": taxPoints(Number(r.taxBps || 0)),
    weights: weightsPoints(r.weights),
    airdrop: airdropPoints(r.gifts),
    pair: pairPoints(r),
    "opening buy": openingPoints(r),
    distribution: distributionPoints(r),
  };
  const total = Object.keys(SCORE_WEIGHTS).reduce(
    (acc, k) => acc + (parts[k][0] * SCORE_WEIGHTS[k]) / 100,
    0
  );
  const score = Math.round(total);
  const lost = Object.entries(parts)
    .map(([k, v]) => [(100 - v[0]) * (SCORE_WEIGHTS[k] / 100), k, v[1]])
    .filter(([l]) => l > 0)
    .sort((a, b) => b[0] - a[0]);
  const notes = lost.slice(0, 3).map(([, , t]) => t);

  let verdict;
  if (score >= 85) verdict = "Well built. This is the configuration of a launch that reaches graduation and keeps holders.";
  else if (score >= 70) verdict = "Solid setup. One or two changes would meaningfully improve your odds.";
  else if (score >= 50) verdict = "Workable, but there are visible leaks — fix the top items before you launch.";
  else verdict = "This configuration works against you. Rework the red items first.";

  const breakdown = {};
  for (const [k, v] of Object.entries(parts)) breakdown[k] = Math.round(v[0]);
  return { score, verdict, notes, breakdown, eta: etaText(r) };
}
