"""Render the score card and the radar card with real data (smoke test)."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bot import api, radar  # noqa: E402
from bot.cards import render_radar_card, render_score_card  # noqa: E402
from bot.curve import fmt_eth, fmt_tokens  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out")


def main() -> int:
    os.makedirs(OUT, exist_ok=True)

    rows = radar.build("FINAL_STRETCH", limit=8)
    table = []
    for r in rows:
        table.append(
            {
                "symbol": r["symbol"],
                "name": r["name"] or "",
                "pair": (r["pairSymbol"] or "?")[:6],
                "progress_bps": r["progress"],
                "to_grad": (
                    f"{fmt_eth(r['toGrad'], 3)} ETH"
                    if r["pairIsNative"]
                    else f"{fmt_tokens(r['toGrad'])} {str(r['pairSymbol'] or '')[:4]}"
                ).strip(),
                "is_native": r["pairIsNative"],
            }
        )
    p1 = os.path.join(OUT, "radar_demo.png")
    render_radar_card(table, p1, "FINAL STRETCH")
    print("radar:", p1, os.path.getsize(p1))

    score = {
        "score": 78,
        "symbol": "CHESS",
        "name": "Chess by vibe",
        "verdict": "Solid launch setup. Two changes could double your holder count.",
        "notes": [
            "Tax 2% is fine, but 75% of it goes to holders — good for retention.",
            "No graduation airdrop configured: you are leaving 20 points on the table.",
            "Opening buy is 0 — buyers read that as low conviction.",
        ],
        "breakdown": {"tax fit": 80, "weights": 88, "airdrop": 0, "pair": 90},
        "footer": "vibegrade · launch score",
    }
    p2 = os.path.join(OUT, "score_demo.png")
    render_score_card(score, p2)
    print("score:", p2, os.path.getsize(p2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
