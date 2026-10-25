"""Render a graduation card for a real, already-graduated launch (smoke test for bot/cards.py)."""
from __future__ import annotations

import json
import os
import sys
import urllib.request
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bot.api import PROXY, media_url  # noqa: E402
from bot.cards import render_graduation_card  # noqa: E402
from bot.curve import fmt_tokens  # noqa: E402

WAD = 10 ** 18
LAUNCHES = os.path.expanduser("~/vibe-docs/api/all_launches.json")
OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out")


def fetch_image(cid: str, dest: str) -> str | None:
    if not cid:
        return None
    opener = urllib.request.build_opener(
        urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
    )
    try:
        with opener.open(urllib.request.Request(media_url(cid, "sq544.webp"), headers={"User-Agent": "Mozilla/5.0"}), timeout=30) as r:
            data = r.read()
        with open(dest, "wb") as f:
            f.write(data)
        return dest
    except Exception as e:  # noqa: BLE001
        print("image failed:", e)
        return None


def human_delta(a: str, b: str) -> str:
    t0 = datetime.fromisoformat(a.replace("Z", "+00:00"))
    t1 = datetime.fromisoformat(b.replace("Z", "+00:00"))
    s = int((t1 - t0).total_seconds())
    if s < 90:
        return f"{s}s"
    if s < 5400:
        return f"{s // 60}m"
    return f"{s // 3600}h {(s % 3600) // 60}m"


def main() -> int:
    os.makedirs(OUT, exist_ok=True)
    data = json.load(open(LAUNCHES, encoding="utf-8"))
    rows = [v for v in data.values() if v.get("graduated") and v.get("graduation") and v.get("market")]
    rows.sort(key=lambda r: int(r["market"].get("holderCount") or 0), reverse=True)
    r = rows[0]
    token = r["tokenAddress"]
    img = fetch_image(r.get("image"), os.path.join(OUT, f"{token}.webp"))

    pair_units = int(r["graduation"]["pairUnits"]) / WAD
    grad = {
        "symbol": r["symbol"],
        "name": r.get("name") or "",
        "image_path": img,
        "time_to_grad": human_delta(r["createdAt"], r["graduation"]["at"]),
        "holders": f"{int(r['market']['holderCount']):,}",
        "volume": fmt_tokens(int(r['market'].get('volume24hPairUnits') or 0)),
        "hero": f"{pair_units:,.2f} {(r.get('pairSymbol') or 'ETH')} RAISED  ·  {fmt_tokens(int(r['graduation']['tokenUnits']))} INTO LP",
        "footer_left": f"{token[:6]}…{token[-4:]}  ·  robinhood chain testnet",
        "footer_right": "vibegrade",
    }
    out = os.path.join(OUT, "grad_demo.png")
    render_graduation_card(grad, out)
    print("rendered:", out, os.path.getsize(out), "bytes")
    print("for:", r["symbol"], r.get("name"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
