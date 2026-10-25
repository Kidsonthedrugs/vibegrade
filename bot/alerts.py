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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bot import api, telegram  # noqa: E402
from bot.curve import fmt_eth, fmt_tokens, pair_to_graduation, progress_bps  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE = os.path.join(ROOT, "data", "alerts.json")
APP = "https://vibegrade-eta.vercel.app"
THRESHOLDS = (9000, 9900)  # bps


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

    fired = 0
    for r in rows:
        prog = progress_bps(r["pairPrincipal"], r["target"])
        done = int(state.get(r["token"], 0))
        for th in THRESHOLDS:
            if prog >= th and done < th:
                left = pair_to_graduation(r["pairPrincipal"], r["target"])
                left_s = (
                    f"{fmt_eth(left, 4)} ETH"
                    if r.get("pairIsNative")
                    else f"{fmt_tokens(left)} {r.get('pairSymbol') or ''}".strip()
                )
                holders = int((r.get("market") or {}).get("holderCount") or 0)
                text = (
                    f"{'🚨' if th == 9900 else '⚡'} <b>{r['symbol']}</b> is "
                    f"<b>{prog / 100:.1f}%</b> to graduation\n"
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
                done = th
                fired += 1

    if not dry:
        save(state)
    print(f"{fired} alert(s) fired")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
