"""Measure the last N hours of graduation activity so posting volume is a number, not a guess."""
from __future__ import annotations

import collections
import os
import sys
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bot import api  # noqa: E402
from bot.curve import pair_to_graduation, progress_bps  # noqa: E402
from bot.watch import MAX_AGE_HOURS, MIN_HOLDERS  # noqa: E402

WAD = 10 ** 18


def hydrate(r: dict) -> dict:
    if (r.get("graduation") or {}).get("at"):
        return r
    try:
        det = api.launch(r["token"]).get("launch") or {}
        r["graduation"] = det.get("graduation") or {}
        r["market"] = det.get("market") or r.get("market") or {}
    except Exception:
        pass
    return r


def dt(s):
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except Exception:
        return None


def main() -> int:
    hours = int(sys.argv[1]) if len(sys.argv) > 1 else 24
    now = datetime.now(timezone.utc)
    since = now - timedelta(hours=hours)

    grad_rows = [api.normalise(i) for i in api.board("GRADUATED")]
    grad_rows = [hydrate(r) for r in grad_rows if r.get("kind") == "v6"]
    in_window = []
    for r in grad_rows:
        at = dt((r.get("graduation") or {}).get("at"))
        if at and at >= since:
            created = dt(r.get("createdAt"))
            r["_secs"] = int((at - created).total_seconds()) if created else None
            r["_holders"] = int((r.get("market") or {}).get("holderCount") or 0)
            r["_at"] = at
            in_window.append(r)

    print(f"=== graduations in the last {hours}h: {len(in_window)} ===")
    by_hour = collections.Counter(r["_at"].strftime("%Y-%m-%d %H:00") for r in in_window)
    for h in sorted(by_hour):
        print(f"  {h}  {'█' * by_hour[h]} {by_hour[h]}")

    qualified = [r for r in in_window if r["_holders"] >= MIN_HOLDERS]
    print(f"\nholders >= {MIN_HOLDERS}: {len(qualified)} of {len(in_window)}")
    if in_window:
        hs = sorted(r["_holders"] for r in in_window)
        print(f"holders per graduation: min {hs[0]}, median {hs[len(hs)//2]}, max {hs[-1]}")
        secs = [r["_secs"] for r in in_window if r["_secs"]]
        if secs:
            secs.sort()
            print(f"time to graduate: min {secs[0]//60}m, median {secs[len(secs)//2]//60}m, max {secs[-1]//3600}h")

    # what the posting rules would have produced
    cards = min(3, len([r for r in qualified if (now - r["_at"]).total_seconds() / 3600 <= MAX_AGE_HOURS]))
    print(f"\nposts under current rules: <= 3 cards/run + digest")
    print(f"  per day, if the watcher runs every 10 min: roughly {len(qualified)} card(s) + 1-2 digest(s)")

    # near-graduation right now
    fs_rows = [api.normalise(i) for i in api.board("FINAL_STRETCH")]
    fs_rows = [r for r in fs_rows if r.get("kind") == "v6" and r.get("target")]
    print(f"\n=== on the curve right now ({len(fs_rows)}) ===")
    a90 = a99 = 0
    for r in sorted(fs_rows, key=lambda r: -progress_bps(r["pairPrincipal"], r["target"])):
        p = progress_bps(r["pairPrincipal"], r["target"])
        left = pair_to_graduation(r["pairPrincipal"], r["target"]) / WAD
        pair = "ETH" if r.get("pairIsNative") else (r.get("pairSymbol") or "?")
        mark = "🚨" if p >= 9900 else ("⚡" if p >= 9000 else "  ")
        if p >= 9900:
            a99 += 1
        elif p >= 9000:
            a90 += 1
        print(f"  {mark} {r['symbol'][:12]:<12} {p/100:6.2f}%  {left:,.4f} {pair}")
    print(f"\nalerts that would fire now: {a90} at 90%, {a99} at 99%")

    total_msgs = len(qualified) + a90 + a99
    print(f"\n=== estimate: ~{total_msgs} messages per {hours}h ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
