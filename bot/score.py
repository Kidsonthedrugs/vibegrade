"""Launch Score — a 0-100 judgement of a vibe/vibe V6 launch configuration.

Every component is a documented, inspectable rule (no black box):
  tax fit          20  the base tax tier vs what it does to graduation speed
  weight balance   25  how the 80% project share is routed
  airdrop          20  whether a graduation airdrop is configured at all
  pair             10  ETH (deep, no extra tax) vs a graduated token pair
  opening buy      15  creator conviction vs concentration
  distribution     10  how many wallets actually hold it

The score is advice, not a promise: it does not predict price or returns.
"""
from __future__ import annotations

from bot.curve import CURVE_SUPPLY, fmt_eth, fmt_tokens, pair_to_graduation, progress_bps

WAD = 10 ** 18
BPS = 10_000

WEIGHTS = {
    "tax fit": 20,
    "weights": 25,
    "airdrop": 20,
    "pair": 10,
    "opening buy": 15,
    "distribution": 10,
}


def _clamp(v: float) -> float:
    return max(0.0, min(100.0, v))


def _tax_points(tax_bps: int) -> tuple[float, str]:
    table = {
        100: (85, "1% keeps the most value in every buy — fastest route to graduation, thin creator revenue."),
        200: (100, "2% is the balanced tier: sells stay cheap and the project share still funds a treasury."),
        300: (70, "3% is the most extractive tier; buyers feel it on every trade and graduation slows."),
    }
    if tax_bps in table:
        return table[tax_bps]
    return (40, f"{tax_bps / 100:.2f}% is outside the 1/2/3% tiers that buyers are used to.")


def _weights_points(w: dict) -> tuple[float, str]:
    cash = int(w.get("cashBps") or 0)
    holders = int(w.get("holdersBps") or 0)
    burn = int(w.get("burnBps") or 0)
    holders_pair = int(w.get("holdersPairBps") or 0)
    total = cash + holders + burn + holders_pair
    if total == 0:
        return 0.0, "No project share is routed anywhere — the 80% has nowhere to go."
    community = holders + holders_pair
    score = 0.0
    score += min(60.0, community / BPS * 80)          # community share, capped
    score += 25.0 if 5 <= cash / BPS * 100 <= 50 else 10.0   # a real treasury, not a hoard
    score += 15.0 if burn <= 20 else 5.0                      # burns are cosmetic beyond 20%
    if cash == BPS:
        score = 35.0
        note = "100% to the treasury: nothing rewards holders, so there is no reason to hold."
    else:
        note = (
            f"{community / 100:.0f}% to holders, {cash / 100:.0f}% to treasury, {burn / 100:.0f}% burned."
            if community >= 4000
            else f"Only {community / 100:.0f}% reaches holders — the token has no holder incentive."
        )
    return _clamp(score), note


def _airdrop_points(gifts: dict) -> tuple[float, str]:
    count = int(gifts.get("count") or 0)
    reserved = int(gifts.get("reservedUnits") or 0)
    if count == 0 or reserved == 0:
        return 0.0, (
            "No graduation airdrop configured. This is the single biggest lever: it is what turns "
            "strangers into holders the moment the curve completes."
        )
    pct = reserved / (CURVE_SUPPLY / WAD * (1000 / 800)) * 100  # share of the 1B supply
    return _clamp(min(100.0, 40 + pct * 12)), (
        f"Airdrop reserved for {count:,} wallets (~{pct:.1f}% of supply) — good, distribution is designed in."
    )


def _pair_points(r: dict) -> tuple[float, str]:
    if r.get("pairIsNative"):
        return 100.0, "Paired against ETH: deepest liquidity and no second tax on every trade."
    return 55.0, (
        f"Paired against {r.get('pairSymbol') or 'a token'}: every trade also pays that token's own tax, "
        "so buyers pay twice and the route is thinner."
    )


def _opening_points(r: dict) -> tuple[float, str]:
    net = int(r.get("netPersonal") or 0)
    supply = 1_000 * 10 ** 6 * WAD
    share = net / supply * 100
    if net == 0:
        return 30.0, (
            "No opening buy: the creator holds nothing, and buyers read that as low conviction. "
            "A small buy at creation is the cheapest signal you can send."
        )
    if share < 0.5:
        return 100.0, f"Opening buy is {share:.2f}% of supply — skin in the game without cornering the float."
    if share <= 10:
        return 80.0, f"Opening buy is {share:.2f}% of supply — fine, watch the concentration."
    return 45.0, (
        f"Opening buy is {share:.1f}% of supply — that much in one wallet scares off the second buyer."
    )


def _distribution_points(r: dict) -> tuple[float, str]:
    holders = int((r.get("market") or {}).get("holderCount") or 0)
    if holders == 0:
        return 55.0, "No holder data yet — neutral."
    if holders >= 500:
        return 100.0, f"{holders:,} holders — healthy, organic-looking distribution."
    if holders >= 100:
        return 85.0, f"{holders:,} holders — solid base."
    if holders >= 30:
        return 60.0, f"{holders:,} holders — early, needs a distribution push."
    return 30.0, f"Only {holders} holders — the curve is being filled by very few wallets."


def _eta_text(r: dict) -> str:
    vol = int((r.get("market") or {}).get("volume24hPairUnits") or 0)
    need = pair_to_graduation(r.get("pairPrincipal") or 0, r.get("target") or 0)
    if vol <= 0 or need <= 0:
        return "—"
    minutes = (need / WAD) / (vol / WAD / 1440)
    if minutes < 60:
        return f"~{minutes:.0f} min at the current 24h pace"
    if minutes < 6000:
        return f"~{minutes / 60:.1f} h at the current 24h pace"
    return f"~{minutes / 1440:.1f} days at the current 24h pace"


def score_launch(r: dict) -> dict:
    """r is a normalised launch (see bot/api.normalise)."""
    parts: dict[str, tuple[float, str]] = {
        "tax fit": _tax_points(int(r.get("taxBps") or 0)),
        "weights": _weights_points(r.get("weights") or {}),
        "airdrop": _airdrop_points(r.get("gifts") or {}),
        "pair": _pair_points(r),
        "opening buy": _opening_points(r),
        "distribution": _distribution_points(r),
    }

    total = sum(parts[k][0] * WEIGHTS[k] / 100 for k in WEIGHTS)
    score = int(round(total))

    # rank the notes by how much score they are costing
    lost = sorted(
        ((100 - v[0]) * WEIGHTS[k] / 100, k, v[1]) for k, v in parts.items() if 100 - v[0] > 0
    )
    notes = [text for _, _, text in lost[:3]]

    if score >= 85:
        verdict = "Well built. This is the configuration of a launch that reaches graduation and keeps holders."
    elif score >= 70:
        verdict = "Solid setup. One or two changes would meaningfully improve your odds."
    elif score >= 50:
        verdict = "Workable, but there are visible leaks — fix the top items before you launch."
    else:
        verdict = "This configuration works against you. Rework the red items first."

    return {
        "score": score,
        "verdict": verdict,
        "notes": notes,
        "breakdown": {k: int(round(v[0])) for k, v in parts.items()},
        "weights": WEIGHTS,
        "eta": _eta_text(r),
        "progress": progress_bps(r.get("pairPrincipal") or 0, r.get("target") or 0),
        "to_graduation": fmt_eth(pair_to_graduation(r.get("pairPrincipal") or 0, r.get("target") or 0), 4)
        if r.get("pairIsNative")
        else fmt_tokens(pair_to_graduation(r.get("pairPrincipal") or 0, r.get("target") or 0)),
    }
