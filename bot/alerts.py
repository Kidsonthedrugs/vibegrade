"""Graduation alerts: ping the channel when a launch gets close to completing its curve.

Thresholds are crossed once each, tracked in data/alerts.json so a restart or a
re-run never repeats an alert.

    python -m bot.alerts            # check + post
    python -m bot.alerts --dry      # check only
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bot import api, telegram  # noqa: E402
from bot.curve import fmt_eth, fmt_tokens, pair_to_graduation, progress_bps  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(ROOT, "data", "alerts.json")
APP = "https://vibegrade-eta.vercel.app"
# Measured reality: ~115 graduations/day, so "alert at 90%" would be ~230 messages/day.
# Only the last stretch is actionable, and only a few per day are worth a ping.
THRESHOLDS = (9900,)        # bps
MAX_ALERTS_PER_DAY = 6      # hard budget, highest progress wins


def _parse(s):
    try:
        return datetime.fromisoformat(str(s).replace("Z", "+00:00"))
    except Exception:
        return None


def load() -> dict:
    try:
        with open(STATE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save(state: dict) -> None:
    os.makedirs(os.path.dirname(STATE), exist_ok=True)
    with open(STATE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=1)


def main() -> int:
    dry = "--dry" in sys.argv
    global THRESHOLDS
    if "--th" in sys.argv:  # manual threshold override, e.g. --th 8800
        THRESHOLDS = (int(sys.argv[sys.argv.index("--th") + 1]),)
    state = load()
    rows = [api.normalise(i) for i in api.board("FINAL_STRETCH")]
    rows = [r for r in rows if r.get("kind") == "v6" and r.get("target") and not r.get("graduated")]

    # daily budget: keep only the most recent N alerts in the window
    hist = [t for t in (state.get("_sent") or [])
            if _parse(t) and (datetime.now(timezone.utc) - _parse(t)).total_seconds() < 86400]
    budget = max(0, MAX_ALERTS_PER_DAY - len(hist))
    rows.sort(key=lambda r: -progress_bps(r["pairPrincipal"], r["target"]))

    fired = 0
    for r in rows:
        if budget <= 0:
            break
        prog = progress_bps(r["pairPrincipal"], r["target"])
        done = int(state.get(r["token"], 0))
        # fire only the highest threshold crossed, never one message per threshold
        crossed = [th for th in THRESHOLDS if prog >= th and done < th]
        if not crossed:
            continue
        th = max(crossed)
        left = pair_to_graduation(r["pairPrincipal"], r["target"])
        left_s = (
            f"{fmt_eth(left, 4)} ETH"
            if r.get("pairIsNative")
            else f"{fmt_tokens(left)} {r.get('pairSymbol') or ''}".strip()
        )
        holders = int((r.get("market") or {}).get("holderCount") or 0)
        text = (
            f"{'🚨' if th >= 9900 else '⚡'} <b>{r['symbol']}</b> is "
            f"<b>{prog / 100:.2f}%</b> to graduation\n"
            f"<i>{r.get('name') or ''}</i>\n"
            f"━━━━━━━━━━━━\n"
            f"🎯 <b>{left_s}</b> left on the curve\n"
            f"👥 {holders:,} holders · tax {r['taxBps'] / 100:.0f}% · "
            f"{'ETH' if r.get('pairIsNative') else r.get('pairSymbol') or '?'} pair\n"
            f"━━━━━━━━━━━━\n"
            f'<a href="{APP}/#token/{r["token"]}">watch it live</a>'
        )
        print(("DRY " if dry else "") + f"{r['symbol']} {prog/100:.2f}% (fired {th/100:.0f}%)")
        if not dry:
            try:
                telegram.send_message(text)
            except Exception as e:  # noqa: BLE001
                print(f"  send failed: {e}")
                continue
        state[r["token"]] = th
        hist.append(datetime.now(timezone.utc).isoformat())
        state["_sent"] = hist
        budget -= 1
        fired += 1

    if not dry:
        save(state)
    print(f"{fired} alert(s) fired")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
