"""Render a shareable Launch Score card for a real token.

    python scripts/score_card.py 0x<token> [more addresses...]
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bot import api, telegram  # noqa: E402
from bot.cards import render_score_card  # noqa: E402
from bot.score import score_launch  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out")


def build(token: str) -> tuple[dict, str]:
    detail = api.launch(token)["launch"]
    row = api.normalise({"kind": "v6", "launch": detail})
    for tab in ("FINAL_STRETCH", "NEW", "TRENDING", "GRADUATED"):
        try:
            hit = next(
                (api.normalise(i) for i in api.board(tab) if api.normalise(i).get("token") == token),
                None,
            )
        except Exception:
            hit = None
        if hit and hit.get("market"):
            row["market"] = hit["market"]
            break
    s = score_launch(row)
    card = {
        "score": s["score"],
        "symbol": row["symbol"],
        "name": row.get("name") or "",
        "verdict": s["verdict"],
        "notes": s["notes"],
        "breakdown": s["breakdown"],
        "footer": f"vibegrade · launch score · {s['eta']}",
    }
    path = os.path.join(OUT, f"score_{row['symbol']}.png")
    render_score_card(card, path)
    return row, path


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    args = sys.argv[1:]
    if not args:
        rows = [api.normalise(i) for i in api.board("FINAL_STRETCH")]
        args = [r["token"] for r in rows if r.get("kind") == "v6"][:1]
    for tok in args:
        row, path = build(tok)
        print(f"{row['symbol']:<10} -> {path}")
