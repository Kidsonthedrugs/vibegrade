"""Parity test: bot/curve.py must match the same on-chain vectors as core/curve.js."""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bot.curve import quote_buy, quote_sell, virtual_token, virtual_pair  # noqa: E402

JSON_PATH = os.environ.get(
    "RPC_JSON",
    os.path.expanduser("~/vibe-docs/rpc_curve_math.json"),
)


def words(h):
    h = h[2:] if h.startswith("0x") else h
    return [int(h[i:i + 64], 16) for i in range(0, len(h), 64)]


def main() -> int:
    with open(JSON_PATH, encoding="utf-8") as f:
        raw = json.load(f)
    g = lambda k: words(raw[k])  # noqa: E731

    st = dict(
        pair_principal=g("SWAG:pairPrincipal()")[0],
        sold=g("SWAG:sold()")[0],
        target=g("SWAG:targetPairUnits()")[0],
        tax_bps=g("SWAG:baseTaxBps()")[0],
    )
    passed = failed = 0
    for amt in ("0.001", "0.01", "0.1", "1.0"):
        w = g(f"SWAG:quoteBuy:{amt}")
        amount_in = int(round(float(amt) * 1e6)) * 10 ** 12
        q = quote_buy(amount_in=amount_in, **st)
        err = abs(q["tokens"] - w[0]) / w[0]
        ok = err < 1e-15 and q["cost"] == w[2]
        passed, failed = (passed + 1, failed) if ok else (passed, failed + 1)
        print(("✅" if ok else "❌") + f" buy {amt}  rel={err:.2e}  cost={'exact' if q['cost']==w[2] else q['cost']-w[2]}")

    w = g("SWAG:quoteSell:1000")
    q = quote_sell(tokens=1000 * 10 ** 18, **st)
    ok = abs(q["proceeds"] - w[1]) <= 2 and abs(q["pair"] - w[3]) <= 2
    passed, failed = (passed + 1, failed) if ok else (passed, failed + 1)
    print(("✅" if ok else "❌") + f" sell 1000  proceeds diff={q['proceeds']-w[1]}  pairOut diff={q['pair']-w[3]}")

    vt, vp = virtual_token(st["target"]), virtual_pair(st["target"])
    remaining = (vt * vp) // (vp + st["target"])
    sold_at_grad = vt - remaining
    want = 800 * 10 ** 6 * 10 ** 18
    ok = abs(sold_at_grad - want) / want < 1e-18
    passed, failed = (passed + 1, failed) if ok else (passed, failed + 1)
    print(("✅" if ok else "❌") + f" graduation invariant  sold={sold_at_grad}")

    print(f"\n{passed} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
