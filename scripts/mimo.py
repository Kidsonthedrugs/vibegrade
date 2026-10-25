"""Ask a cheap model (mimo v2.6 pro via 9Router) to write a file, then save it.

Usage:
    python scripts/mimo.py <prompt_file> <target_path> [--model MODEL] [--context FILE ...]

Notes (learned the hard way):
  * mimo-v2.6-FLASH is broken on this gateway ("Failed to convert streaming response"),
    so the default is mimo-v2.6-pro.
  * Every call carries ~7.4k tokens of gateway system prompt -> batch big asks,
    avoid many tiny requests.
  * Output is expected as a single fenced code block; the first one wins.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.request

ROUTER = "http://127.0.0.1:20128/v1/chat/completions"
ENV = os.path.expanduser("~/AppData/Local/hermes/.env")
DEFAULT_MODEL = "cmc/xiaomi/mimo-v2.6-pro"


def api_key() -> str:
    with open(ENV, encoding="utf-8", errors="replace") as f:
        for line in f:
            if line.startswith("HERMES_CUSTOM_9ROUTER_LOCAL_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("9router api key not found in .env")


def ask(prompt: str, model: str, max_tokens: int = 8192) -> str:
    body = json.dumps(
        {
            "model": model,
            "stream": False,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
        }
    ).encode()
    req = urllib.request.Request(
        ROUTER,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key()}",
        },
    )
    with urllib.request.urlopen(req, timeout=600) as r:
        j = json.load(r)
    return j["choices"][0]["message"]["content"]


def extract_code(text: str) -> str:
    blocks = re.findall(r"```(?:python|py)?\n(.*?)```", text, re.S)
    if blocks:
        return max(blocks, key=len).strip() + "\n"
    return text.strip() + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("prompt_file")
    ap.add_argument("target")
    ap.add_argument("--model", default=DEFAULT_MODEL)
    ap.add_argument("--context", action="append", default=[])
    ap.add_argument("--max-tokens", type=int, default=8192)
    args = ap.parse_args()

    prompt = open(args.prompt_file, encoding="utf-8").read()
    for c in args.context:
        prompt += f"\n\n--- EXISTING FILE: {c} ---\n" + open(c, encoding="utf-8").read()

    out = ask(prompt, args.model, args.max_tokens)
    code = extract_code(out)
    os.makedirs(os.path.dirname(os.path.abspath(args.target)), exist_ok=True)
    with open(args.target, "w", encoding="utf-8") as f:
        f.write(code)
    print(f"wrote {args.target} ({len(code)} chars)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
