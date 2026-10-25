"""Proxy-aware client for the vibe/vibe testnet API (Iran-safe: always via Nekoray 2081)."""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request

CHAIN_ID = 46630
BASE = "https://testnet.vibevibe.fun"
PROXY = os.environ.get("NEKORAY_PROXY", "http://127.0.0.1:2081")
HDR = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0 Safari/537.36",
    "accept": "application/json",
    "Origin": BASE,
    "Referer": BASE + "/",
}

_opener = urllib.request.build_opener(
    urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
)


def get(path: str, tries: int = 4, timeout: int = 30):
    url = path if path.startswith("http") else BASE + path
    last = ""
    for i in range(tries):
        try:
            with _opener.open(urllib.request.Request(url, headers=HDR), timeout=timeout) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            last = f"HTTP {e.code} {url}"
            if e.code in (400, 404):
                break
            time.sleep(1.5 + i * 2)
        except Exception as e:  # noqa: BLE001
            last = f"{type(e).__name__}: {e}"
            time.sleep(1.5 + i * 2)
    raise RuntimeError(last)


def board(tab: str = "FINAL_STRETCH"):
    j = get(f"/api/v1/chains/{CHAIN_ID}/board?tab={tab}")
    return j.get("data", {}).get("items", [])


def launch(token: str):
    return get(f"/api/v1/chains/{CHAIN_ID}/v6/launches/{token}").get("data", {})


def eth_usd() -> float:
    j = get(f"/api/v1/chains/{CHAIN_ID}/market/eth-usd")
    return int(j["data"]["usdPerEthCents"]) / 100


def normalise(item: dict) -> dict:
    l = item.get("launch") or item
    curve = l.get("curve") or {}
    return {
        "token": l.get("tokenAddress"),
        "curve": l.get("curveAddress"),
        "name": l.get("name"),
        "symbol": l.get("symbol"),
        "image": ((l.get("content") or {}).get("image") or {}).get("uri"),
        "pairSymbol": l.get("pairSymbol"),
        "pairIsNative": bool(l.get("pairIsNative")),
        "target": int(l.get("targetPairUnits") or 0),
        "sold": int(curve.get("tokensSoldGrossUnits") or 0),
        "pairPrincipal": int(curve.get("pairReserveUnits") or 0),
        "taxBps": int(l.get("taxBps") or 0),
        "lifecycle": l.get("lifecycle"),
        "graduated": bool(l.get("graduated")),
        "createdAt": l.get("createdAt"),
        "createdBlock": l.get("createdBlock"),
        "market": l.get("market") or {},
        "weights": l.get("weights") or {},
        "gifts": l.get("gifts") or {},
        "launcher": l.get("launcherAddress"),
    }


def media_url(cid: str | None, variant: str = "card.webp") -> str | None:
    if not cid:
        return None
    return f"{BASE}/media/{cid.replace('ipfs://', '')}.{variant}"
