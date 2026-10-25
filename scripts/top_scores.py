"""Pick the most-watched launches, score them, post cards, write tweet copy.

    python scripts/top_scores.py            # build + post
    python scripts/top_scores.py --dry      # build only
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bot import api, telegram  # noqa: E402
from bot.cards import render_score_card  # noqa: E402
from bot.score import score_launch  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "out")


def pick(n: int = 3) -> list[dict]:
    rows: dict[str, dict] = {}
    for tab in ("TRENDING", "FINAL_STRETCH", "GRADUATED"):
        for item in api.board(tab):
            r = api.normalise(item)
            if r.get("kind") != "v6" or not r.get("token"):
                continue
            if r["token"] not in rows or (not rows[r["token"]].get("market") and r.get("market")):
                rows[r["token"]] = r
    def heat(r):
        m = r.get("market") or {}
        return (int(m.get("holderCount") or 0), int(m.get("volume24hPairUnits") or 0))
    return sorted(rows.values(), key=heat, reverse=True)[:n]


def main() -> int:
    dry = "--dry" in sys.argv
    os.makedirs(OUT, exist_ok=True)
    tweets = []
    for r in pick(3):
        s = score_launch(r)
        card = os.path.join(OUT, f"score_{r['symbol']}.png")
        render_score_card(
            {
                "score": s["score"],
                "symbol": r["symbol"],
                "name": r.get("name") or "",
                "verdict": s["verdict"],
                "notes": s["notes"],
                "breakdown": s["breakdown"],
                "footer": f"vibegrade · launch score · {s['eta']}",
            },
            card,
        )
        holders = int((r.get("market") or {}).get("holderCount") or 0)
        caption = (
            f"<b>{r['symbol']}</b> scores <b>{s['score']}/100</b> on the VibeGrade launch score\n"
            f"<i>{r.get('name') or ''} · {holders:,} holders · tax {r['taxBps']/100:.0f}% · "
            f"{r.get('pairSymbol') or '?'} pair</i>\n"
            f"━━━━━━━━━━━━\n"
            + "\n".join("• " + n for n in s["notes"][:2])
            + f'\n━━━━━━━━━━━━\n<a href="https://vibegrade-eta.vercel.app/?token={r["token"]}&tab=score">score any token</a>'
        )
        if not dry:
            telegram.send_photo(card, caption)
        print(f"{r['symbol']:<10} {s['score']:>3}/100  -> {card}")

        worst = min(s["breakdown"], key=lambda k: s["breakdown"][k])
        tweets.append(
            f"{r['symbol']} scores {s['score']}/100 on launch quality.\n\n"
            f"{holders:,} holders · {r['taxBps']/100:.0f}% tax · {'ETH' if r.get('pairIsNative') else r.get('pairSymbol')} pair\n"
            f"Weakest part: {worst} ({s['breakdown'][worst]}/100).\n\n"
            f"Scored with @vibevibefun's own curve math → vibegrade-eta.vercel.app"
        )

    with open(os.path.join(OUT, "tweets_top3.txt"), "w", encoding="utf-8") as f:
        f.write("\n\n---\n\n".join(tweets) + "\n")
    print("\nwrote", os.path.join(OUT, "tweets_top3.txt"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
