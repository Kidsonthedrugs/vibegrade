"""Count real graduations in the last N hours by paging the board, not by trusting one page."""
from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

P = os.environ.get("NEKORAY_PROXY", "http://127.0.0.1:2081")
op = urllib.request.build_opener(urllib.request.ProxyHandler({"http": P, "https": P}))
HDR = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/131.0 Safari/537.36",
    "accept": "application/json",
    "Origin": "https://testnet.vibevibe.fun",
}
BASE = "https://testnet.vibevibe.fun/api/v1/chains/46630"


def get(path: str, tries: int = 3):
    for i in range(tries):
        try:
            with op.open(urllib.request.Request(BASE + path, headers=HDR), timeout=40) as r:
                return json.loads(r.read())
        except Exception:
            if i == tries - 1:
                return None
    return None


def dt(s):
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except Exception:
        return None


def main() -> int:
    hours = int(sys.argv[1]) if len(sys.argv) > 1 else 24
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=hours)

    rows, page, total = [], 1, None
    while page <= 12:
        j = get(f"/board?tab=GRADUATED&page={page}")
        if not j:
            print(f"page {page}: failed")
            break
        d = j.get("data", {})
        items = d.get("items", [])
        meta = d.get("page", {})
        total = meta.get("total", total)
        if not items:
            break
        oldest = None
        for it in items:
            l = it.get("launch") or {}
            created = dt(l.get("createdAt"))
            if created and (oldest is None or created < oldest):
                oldest = created
            rows.append(l)
        print(f"page {page:>2}: {len(items)} items · oldest createdAt {oldest:%Y-%m-%d %H:%M} UTC")
        # stop once a whole page predates the window (graduation is always after creation)
        if oldest and oldest < cutoff:
            break
        page += 1

    print(f"\nboard total (all time): {total:,} graduated launches")
    print(f"pulled {len(rows)} launch records from {page} page(s)")

    # a launch created before the cutoff may still have graduated inside the window
    candidates = [l for l in rows if (dt(l.get("createdAt")) or now) >= cutoff - timedelta(hours=12)]
    print(f"candidates to check: {len(candidates)}")

    inside = []
    for i, l in enumerate(candidates, 1):
        tok = l.get("tokenAddress")
        try:
            j = get(f"/v6/launches/{tok}")
            det = (j or {}).get("data", {}).get("launch") or {}
            g = det.get("graduation") or {}
            at = dt(g.get("at"))
            if at and at >= cutoff:
                created = dt(l.get("createdAt"))
                gifts = det.get("gifts") or {}
                mkt = det.get("market") or {}
                inside.append({
                    "symbol": l.get("symbol"),
                    "at": at.isoformat(),
                    "holders": int(mkt.get("holderCount") or l.get("holderCount") or 0),
                    "secs": int((at - created).total_seconds()) if created else None,
                    "airdrop": int(gifts.get("count") or 0) > 0,
                    "token": tok,
                })
        except Exception:
            pass
        if i % 20 == 0:
            print(f"  checked {i}/{len(candidates)} … found {len(inside)}", flush=True)

    inside.sort(key=lambda x: x["at"])
    import json as _json
    out = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "out", f"graduations_{hours}h.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        _json.dump(inside, f, indent=1)
    print(f"saved {len(inside)} rows -> {out}")

    if inside:
        hs = sorted(x["holders"] for x in inside)
        ss = sorted(x["secs"] for x in inside if x["secs"])
        print(f"holders: min {hs[0]} · median {hs[len(hs)//2]} · p90 {hs[int(len(hs)*0.9)]} · max {hs[-1]}")
        if ss:
            print(f"minutes to graduate: median {ss[len(ss)//2]//60} · p10 {ss[len(ss)//10]//60} · min {ss[0]//60}")
        print(f"airdrop configured: {sum(1 for x in inside if x['airdrop'])}")
        for th in (25, 50, 100, 250):
            print(f"  holders >= {th:<4}: {sum(1 for x in inside if x['holders'] >= th)}")
        for m in (5, 10, 30):
            print(f"  under {m:<3}m: {sum(1 for x in inside if x['secs'] and x['secs'] < m*60)}")
        n1 = sum(1 for x in inside if x["holders"] >= 50 or (x["secs"] and x["secs"] < 600) or x["airdrop"])
        n2 = sum(1 for x in inside if x["holders"] >= 100 or (x["secs"] and x["secs"] < 300))
        print(f"\nNOTABLE (holders>=50 | <10m | airdrop): {n1} / {hours}h")
        print(f"STRICT  (holders>=100 | <5m):           {n2} / {hours}h")

    print(f"\n=== REAL graduations in the last {hours}h: {len(inside)} ===")
    per_hour = {}
    for x in inside:
        hh = str(x["at"])[11:16]
        per_hour[hh] = per_hour.get(hh, 0) + 1
    for h in sorted(per_hour):
        print(f"  {h}  {'█' * per_hour[h]} {per_hour[h]}")
    if inside:
        rate = len(inside) / hours
        print(f"\nrate: {rate:.1f} graduations/hour  ->  {rate * 24:.0f} per day")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
