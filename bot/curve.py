"""VibeGrade — bonding-curve math (Python port of core/curve.js).

Verified against live on-chain quotes from Robinhood Chain Testnet.
Buys are fee-on-top; sells deduct tax straight off proceeds. See notes in curve.js.
"""
from __future__ import annotations

WAD = 10 ** 18
BPS = 10_000

CURVE_SUPPLY = 800 * 10 ** 6 * WAD
LP_SUPPLY = 200 * 10 ** 6 * WAD
TOTAL_SUPPLY = 1_000 * 10 ** 6 * WAD


def virtual_token(target: int) -> int:
    return (CURVE_SUPPLY * 4) // 3


def virtual_pair(target: int) -> int:
    return target // 3


def split_fee(amount_in: int, tax_bps: int) -> tuple[int, int]:
    cost = (amount_in * BPS) // (BPS + int(tax_bps))
    return cost, amount_in - cost


def quote_buy(amount_in: int, sold: int, pair_principal: int, target: int, tax_bps: int) -> dict:
    cost, fee = split_fee(amount_in, tax_bps)
    vt = virtual_token(target)
    vp = virtual_pair(target)
    k = vt * vp
    remaining = vt - sold
    tokens = remaining - k // (vp + pair_principal + cost)
    return {"tokens": tokens, "cost": cost, "fee": fee}


def quote_sell(tokens: int, sold: int, pair_principal: int, target: int, tax_bps: int) -> dict:
    vt = virtual_token(target)
    vp = virtual_pair(target)
    proceeds = ((vp + pair_principal) * tokens) // (vt - sold + tokens)
    fee = (proceeds * int(tax_bps)) // BPS
    return {"pair": proceeds - fee, "proceeds": proceeds, "fee": fee}


def spot_price(sold: int, pair_principal: int, target: int) -> int:
    """WAD-scaled pair units per token."""
    return ((virtual_pair(target) + pair_principal) * WAD) // (virtual_token(target) - sold)


def pair_to_graduation(pair_principal: int, target: int) -> int:
    return max(target - pair_principal, 0)


def progress_bps(pair_principal: int, target: int) -> int:
    if target <= 0:
        return 0
    return (pair_principal * BPS) // target


def pair_to_reach_sold(sold: int, pair_principal: int, target: int, want_sold: int) -> int | None:
    vt = virtual_token(target)
    vp = virtual_pair(target)
    remaining_after = vt - want_sold
    if remaining_after <= 0:
        return None
    vp_after = (vt * vp) // remaining_after
    need = vp_after - vp - pair_principal
    return need if need > 0 else 0


def fmt_eth(wei: int, digits: int = 4) -> str:
    whole, frac = divmod(int(wei), WAD)
    s = f"{whole}.{str(frac).zfill(18)[:digits]}".rstrip("0").rstrip(".")
    return s or "0"


def fmt_tokens(base: int) -> str:
    n = base / WAD
    if n >= 1e9:
        return f"{n/1e9:.2f}B"
    if n >= 1e6:
        return f"{n/1e6:.2f}M"
    if n >= 1e3:
        return f"{n/1e3:.1f}K"
    return f"{n:,.0f}"
