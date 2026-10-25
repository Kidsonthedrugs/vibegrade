"""Weekly VibeGrade report: what actually happened on the vibe/vibe testnet.

Computes honest numbers from the public board, renders a card, posts it to the
channel and writes ready-to-post tweet copy next to it.

    python -m bot.report            # build + post
    python -m bot.report --dry      # build only, print, no post
"""
from __future__ import annotations

import json
import os
import statistics
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bot import api, telegram  # noqa: E402
from bot.cards import render_report_card  # noqa: E402
from bot.curve import fmt_tokens  # noqa: E402
from bot.score import score_launch  # noqa: E402

WAD = 10 ** 18
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "out")
DEFAULT_WEIGHTS = {"cashBps": 2000, "holdersBps": 7500, "burnBps": 500, "holdersPairBps": 0}


def sample() -> list[dict]:
    """Union of the public board tabs, deduped, v6 only."""
    seen: dict[str, dict] = {}
    for tab in ("TRENDING", "NEW", "FINAL_STRETCH", "GRADUATED", "MOVERS"):
        try:
            items = api.board(tab)
        except Exception:
            continue
        for item in items:
            r = api.normalise(item)
            if r.get("kind") != "v6" or not r.get("token"):
                continue
            prev = seen.get(r["token"])
            if prev is None or (not prev.get("market") and r.get("market")):
                seen[r["token"]] = r

    rows = list(seen.values())
    # The board omits the graduation block; the launch detail carries it.
    for r in rows:
        if r.get("graduated") and not (r.get("graduation") or {}).get("at"):
            try:
                det = api.launch(r["token"]).get("launch") or {}
                r["graduation"] = det.get("graduation") or {}
                r["market"] = det.get("market") or r.get("market") or {}
            except Exception:
                pass
    return rows


def _dt(s: str | None):
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None


def stats(rows: list[dict], days: int = 7) -> dict:
    now = datetime.now(timezone.utc)
    since = now - timedelta(days=days)

    grads = []
    for r in rows:
        g = r.get("graduation") or {}
        at = _dt(g.get("at"))
        if r.get("graduated") and at and at >= since:
            created = _dt(r.get("createdAt"))
            secs = int((at - created).total_seconds()) if created else None
            grads.append({"row": r, "at": at, "secs": secs, "raised": int(g.get("pairUnits") or 0)})

    fastest = min((g for g in grads if g["secs"]), key=lambda g: g["secs"], default=None)
    # Only native-ETH curves are comparable; other pairs are denominated in their own asset.
    eth_grads = [g for g in grads if g["row"].get("pairIsNative")]
    raised = sum(g["raised"] for g in eth_grads)
    other_grads = len(grads) - len(eth_grads)

    with_airdrop = [r for r in rows if int((r.get("gifts") or {}).get("reservedUnits") or 0) > 0]
    default_w = [
        r
        for r in rows
        if (r.get("weights") or {}) == DEFAULT_WEIGHTS
    ]
    opening_pct = [
        int(r.get("netPersonal") or 0) / (1_000 * 10 ** 6 * WAD) * 100
        for r in rows
        if int(r.get("netPersonal") or 0) > 0
    ]
    holders = [
        int((r.get("market") or {}).get("holderCount") or 0)
        for r in rows
        if (r.get("market") or {}).get("holderCount")
    ]
    over_30 = [p for p in opening_pct if p >= 30]

    return {
        "days": days,
        "sample": len(rows),
        "graduations": len(grads),
        "raised": raised,
        "eth_grads": len(eth_grads),
        "other_grads": other_grads,
        "fastest": fastest,
        "airdrop_pct": (100 * len(with_airdrop) / len(rows)) if rows else 0,
        "default_weights_pct": (100 * len(default_w) / len(rows)) if rows else 0,
        "opening_median": statistics.median(opening_pct) if opening_pct else 0,
        "over_30_pct": (100 * len(over_30) / len(opening_pct)) if opening_pct else 0,
        "median_holders": statistics.median(holders) if holders else 0,
        "top": max(grads, key=lambda g: g["raised"], default=None),
    }


def fmt_dur(secs: int | None) -> str:
    if not secs:
        return "—"
    if secs < 90:
        return f"{secs}s"
    if secs < 5400:
        return f"{secs // 60}m"
    return f"{secs // 3600}h {(secs % 3600) // 60}m"


def build_post(st: dict) -> tuple[str, str]:
    """(caption for telegram, tweet copy)"""
    fast = st["fastest"]
    fast_line = (
        f"⚡ fastest: <b>{fast['row']['symbol']}</b> in <b>{fmt_dur(fast['secs'])}</b>"
        if fast
        else "⚡ no graduations in the window"
    )
    caption = (
        f"📊 <b>VibeGrade · last {st['days']} days</b>\n"
        f"<i>{st['sample']} live launches tracked</i>\n"
        f"━━━━━━━━━━━━\n"
        f"🎓 <b>{st['graduations']}</b> graduations · <b>{fmt_tokens(st['raised'])} ETH</b> raised on ETH pairs\n"
        f"{fast_line}\n"
        f"👥 median holders: <b>{st['median_holders']:.0f}</b>\n"
        f"━━━━━━━━━━━━\n"
        f"🟥 <b>{st['airdrop_pct']:.0f}%</b> of launches configured a graduation airdrop\n"
        f"🟨 <b>{st['over_30_pct']:.0f}%</b> spent 30%+ of the 50% budget on their own opening buy\n"
        f"🟦 <b>{st['default_weights_pct']:.0f}%</b> left the default tax weights untouched\n"
        f"━━━━━━━━━━━━\n"
        f'<a href="https://vibegrade-eta.vercel.app">full radar + launch score</a>'
    )
    tweet = (
        f"Last {st['days']} days on vibe/vibe (Robinhood Chain testnet), measured:\n\n"
        f"· {st['graduations']} graduations ({st['eth_grads']} ETH-paired, {fmt_tokens(st['raised'])} ETH raised)\n"
        f"· median holders per launch: {st['median_holders']:.0f}\n"
        f"· only {st['airdrop_pct']:.0f}% configured a graduation airdrop\n"
        f"· {st['over_30_pct']:.0f}% spent 30%+ of the 50% budget on their own opening buy\n\n"
        f"The 50% budget is meant for distribution. Mostly it goes to the creator.\n\n"
        f"radar + launch score → vibegrade-eta.vercel.app"
    )
    return caption, tweet


def main() -> int:
    dry = "--dry" in sys.argv
    rows = sample()
    st = stats(rows)
    caption, tweet = build_post(st)
    os.makedirs(OUT, exist_ok=True)

    card = os.path.join(OUT, "weekly.png")
    render_report_card(
        {
            "title": f"LAST {st['days']} DAYS",
            "subtitle": f"{st['sample']} live launches tracked · vibe/vibe testnet",
            "stats": [
                (str(st["graduations"]), "GRADUATIONS"),
                (f"{fmt_tokens(st['raised'])} ETH", "RAISED"),
                (f"{st['median_holders']:.0f}", "MEDIAN HOLDERS"),
                (f"{st['airdrop_pct']:.0f}%", "AIRDROP CONFIGURED"),
                (f"{st['over_30_pct']:.0f}%", "SELF-ALLOCATED 30%+"),
                (f"{st['default_weights_pct']:.0f}%", "DEFAULT WEIGHTS"),
            ],
            "footer": "vibegrade · robinhood chain testnet",
        },
        card,
    )
    print(caption.replace("<b>", "").replace("</b>", "").replace("<i>", "").replace("</i>", ""))
    print("\n--- tweet ---\n" + tweet)

    with open(os.path.join(OUT, "weekly_tweet.txt"), "w", encoding="utf-8") as f:
        f.write(tweet + "\n")
    with open(os.path.join(OUT, "weekly_stats.json"), "w", encoding="utf-8") as f:
        json.dump({k: v for k, v in st.items() if k not in ("fastest", "top")}, f, indent=1)

    if not dry:
        telegram.send_photo(card, caption)
        print("\nposted to channel")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
