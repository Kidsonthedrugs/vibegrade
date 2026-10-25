"""Watch the chain for new graduations, render a card, post it. State survives restarts."""
from __future__ import annotations

import json
import os
import sys
import time
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bot import api, telegram  # noqa: E402
from bot.cards import render_graduation_card  # noqa: E402
from bot.curve import fmt_tokens  # noqa: E402

WAD = 10 ** 18
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(ROOT, "data", "state.json")
OUT = os.path.join(ROOT, "out")
APP = "https://testnet.vibevibe.fun"


def load_state() -> dict:
    try:
        with open(STATE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"posted": [], "last_check": None}


def save_state(st: dict) -> None:
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    tmp = STATE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(st, f, indent=1)
    os.replace(tmp, STATE)


def human_delta(a: str, b: str) -> str:
    try:
        t0 = datetime.fromisoformat(a.replace("Z", "+00:00"))
        t1 = datetime.fromisoformat(b.replace("Z", "+00:00"))
    except Exception:
        return "—"
    s = int((t1 - t0).total_seconds())
    if s < 90:
        return f"{s}s"
    if s < 5400:
        return f"{s // 60}m {s % 60}s"
    return f"{s // 3600}h {(s % 3600) // 60}m"


def fetch_image(cid: str | None, dest: str) -> str | None:
    if not cid:
        return None
    import urllib.request

    opener = urllib.request.build_opener(
        urllib.request.ProxyHandler({"http": api.PROXY, "https": api.PROXY})
    )
    try:
        with opener.open(
            urllib.request.Request(api.media_url(cid, "sq544.webp"), headers={"User-Agent": "Mozilla/5.0"}),
            timeout=30,
        ) as r:
            data = r.read()
        with open(dest, "wb") as f:
            f.write(data)
        return dest
    except Exception:
        return None


def build_caption(r: dict, tok: str) -> str:
    grad = r.get("graduation") or {}
    pair = r.get("pairSymbol") or "ETH"
    raised = int(grad.get("pairUnits") or 0) / WAD
    lp = int(grad.get("tokenUnits") or 0)
    vol = int((r.get("market") or {}).get("volume24hPairUnits") or 0)
    return (
        f"🟡 <b>{r['symbol']}</b> just graduated\n"
        f"<i>{r.get('name') or '—'}</i>\n"
        f"━━━━━━━━━━━━\n"
        f"⏱ <b>{human_delta(r['createdAt'], grad.get('at', r['createdAt']))}</b> from launch to graduation\n"
        f"👥 <b>{int((r.get('market') or {}).get('holderCount') or 0):,}</b> holders\n"
        f"💰 <b>{fmt_tokens(raised * WAD)} {pair}</b> raised · {fmt_tokens(lp)} into LP\n"
        f"📊 <b>{fmt_tokens(vol)} {pair}</b> volume (24h)\n"
        f"━━━━━━━━━━━━\n"
        f'<a href="{APP}/t/{tok}">open on vibe/vibe</a>'
    )


def check_once(state: dict, post: bool = True, limit: int | None = None) -> list[dict]:
    """Return newly seen graduated launches; post them when post=True."""
    items = api.board("GRADUATED")
    seen = set(state["posted"])
    fresh: list[dict] = []
    for item in items:
        r = api.normalise(item)
        if not r.get("graduated") or r["token"] in seen:
            continue
        fresh.append(r)
    fresh.sort(key=lambda r: ((r.get("graduation") or {}).get("at") or ""), reverse=True)
    if limit is not None:
        fresh = fresh[:limit]
    if post:
        os.makedirs(OUT, exist_ok=True)
        for r in reversed(fresh):  # oldest first so the channel reads chronologically
            tok = r["token"]
            if not r.get("graduation") or not (r.get("graduation") or {}).get("pairUnits"):
                try:
                    det = api.launch(tok).get("launch") or {}
                    r["graduation"] = det.get("graduation") or r.get("graduation") or {}
                    r["market"] = det.get("market") or r.get("market") or {}
                except Exception as e:  # noqa: BLE001
                    print(f"detail fetch failed for {tok}: {e}")
            img = fetch_image(r.get("image"), os.path.join(OUT, f"{tok}.webp"))
            grad = r.get("graduation") or {}
            card = os.path.join(OUT, f"grad_{tok}.png")
            render_graduation_card(
                {
                    "symbol": r["symbol"],
                    "name": r.get("name") or "",
                    "image_path": img,
                    "time_to_grad": human_delta(r["createdAt"], grad.get("at", r["createdAt"])),
                    "holders": f"{int((r.get('market') or {}).get('holderCount') or 0):,}",
                    "volume": fmt_tokens(int((r.get("market") or {}).get("volume24hPairUnits") or 0)),
                    "hero": (
                        f"{int(grad.get('pairUnits', 0)) / WAD:,.2f} {r.get('pairSymbol') or 'ETH'} RAISED  ·  "
                        f"{fmt_tokens(int(grad.get('tokenUnits', 0)))} INTO LP"
                        if grad.get("pairUnits")
                        else "BONDING CURVE COMPLETE"
                    ),
                    "footer_left": f"{tok[:6]}…{tok[-4:]}  ·  robinhood chain testnet",
                    "footer_right": "vibegrade",
                },
                card,
            )
            try:
                telegram.send_photo(card, build_caption(r, tok))
                state["posted"].append(tok)
                print(f"posted {r['symbol']} {tok}")
            except Exception as e:  # noqa: BLE001
                print(f"FAILED {r['symbol']}: {e}")
            time.sleep(1.5)
    return fresh


def main() -> int:
    state = load_state()
    seed = "--seed" in sys.argv
    limit = None
    if "--limit" in sys.argv:
        limit = int(sys.argv[sys.argv.index("--limit") + 1])
    try:
        if seed:
            fresh = check_once(state, post=False, limit=limit)
            for r in fresh:
                state["posted"].append(r["token"])
            print(f"seeded {len(fresh)} existing graduations (nothing posted)")
        else:
            fresh = check_once(state, post="--no-post" not in sys.argv, limit=limit)
            print(f"{len(fresh)} new graduation(s)")
    finally:
        state["last_check"] = datetime.now(timezone.utc).isoformat()
        save_state(state)
    print(f"total posted: {len(state['posted'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
