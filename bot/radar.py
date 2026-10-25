"""Radar: rank live launches by how close they are to graduation (exact, from the curve math)."""
from __future__ import annotations

import sys
from datetime import datetime, timezone

from bot import api
from bot.curve import fmt_eth, fmt_tokens, pair_to_graduation, progress_bps, spot_price

WAD = 10 ** 18


def eta_minutes(row: dict) -> float | None:
    """Rough ETA from the last 24h pair inflow. None when there is no flow yet."""
    vol = int((row.get("market") or {}).get("volume24hPairUnits") or 0)
    if vol <= 0:
        return None
    per_min = vol / 1440
    if per_min <= 0:
        return None
    need = pair_to_graduation(row["pairPrincipal"], row["target"]) / WAD
    return need / per_min


def build(tab: str = "FINAL_STRETCH", limit: int = 12) -> list[dict]:
    rows = [api.normalise(i) for i in api.board(tab)]
    rows = [r for r in rows if r["target"] > 0 and not r["graduated"]]
    for r in rows:
        r["toGrad"] = pair_to_graduation(r["pairPrincipal"], r["target"])
        r["progress"] = progress_bps(r["pairPrincipal"], r["target"])
        r["eta"] = eta_minutes(r)
        r["price"] = spot_price(r["sold"], r["pairPrincipal"], r["target"])
    rows.sort(key=lambda r: r["toGrad"])
    return rows[:limit]


def render(rows: list[dict], eth_price: float | None = None) -> str:
    out = []
    head = f"{'#':>2} {'SYM':<10} {'PAIR':<9} {'PROGRESS':>9} {'TO GRAD':>16} {'ETA':>7}"
    out.append(head)
    out.append("-" * len(head))
    for i, r in enumerate(rows, 1):
        if r["eta"] is None:
            eta = "—"
        elif r["eta"] < 1:
            eta = "<1m"
        elif r["eta"] < 6000:
            eta = f"{r['eta']:.0f}m"
        else:
            eta = ">4d"
        pair = str(r["pairSymbol"] or "?")[:6]
        if r["pairIsNative"]:
            to_grad = f"{fmt_eth(r['toGrad'], 4)} ETH"
        else:
            to_grad = f"{fmt_tokens(r['toGrad'])} {pair}"
        out.append(
            f"{i:>2} {r['symbol'][:10]:<10} {pair:<9} "
            f"{r['progress']/100:>8.2f}% {to_grad:>16} {eta:>7}"
        )
    if eth_price:
        out.append(f"\nETH = ${eth_price:,.0f}")
    return "\n".join(out)


if __name__ == "__main__":
    tab = sys.argv[1] if len(sys.argv) > 1 else "FINAL_STRETCH"
    try:
        px = api.eth_usd()
    except Exception:
        px = None
    rows = build(tab)
    print(f"VibeGrade radar · {tab} · {datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC} · {len(rows)} launches\n")
    print(render(rows, px))
