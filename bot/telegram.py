"""Telegram poster for VibeGrade (always through the Nekoray proxy)."""
from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request

PROXY = os.environ.get("NEKORAY_PROXY", "http://127.0.0.1:2081")
ENV = os.path.expanduser("~/AppData/Local/hermes/.env")
CHANNEL = os.environ.get("VIBEGRADE_CHANNEL", "-1004398672746")
CHANNEL_HANDLE = "@VibeGraduation"

_opener = urllib.request.build_opener(
    urllib.request.ProxyHandler({"http": PROXY, "https": PROXY})
)


def token() -> str:
    with open(ENV, encoding="utf-8", errors="replace") as f:
        for line in f:
            if line.startswith("TELEGRAM_BOT_TOKEN="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise RuntimeError("TELEGRAM_BOT_TOKEN not found")


def _api(method: str, payload: dict, tries: int = 3):
    url = f"https://api.telegram.org/bot{token()}/{method}"
    body = json.dumps(payload).encode()
    last = ""
    for i in range(tries):
        try:
            req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
            with _opener.open(req, timeout=60) as r:
                return json.loads(r.read())
        except urllib.error.HTTPError as e:
            detail = e.read()[:300].decode("utf-8", "replace")
            last = f"HTTP {e.code}: {detail}"
            if e.code == 429:
                time.sleep(5 * (i + 1))
                continue
            break
        except Exception as e:  # noqa: BLE001
            last = f"{type(e).__name__}: {e}"
            time.sleep(2 + i * 2)
    raise RuntimeError(f"{method} failed: {last}")


def send_message(text: str, chat_id: str | None = None, preview: bool = True):
    return _api(
        "sendMessage",
        {
            "chat_id": chat_id or CHANNEL,
            "text": text,
            "parse_mode": "HTML",
            "disable_web_page_preview": not preview,
        },
    )


def send_photo(path: str, caption: str, chat_id: str | None = None):
    """multipart upload without external deps."""
    boundary = "----vibegrade" + str(int(time.time() * 1000))
    with open(path, "rb") as f:
        photo = f.read()
    parts: list[bytes] = []
    for name, value in (
        ("chat_id", chat_id or CHANNEL),
        ("caption", caption),
        ("parse_mode", "HTML"),
    ):
        parts.append(
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"{name}\"\r\n\r\n{value}\r\n".encode()
        )
    parts.append(
        f"--{boundary}\r\nContent-Disposition: form-data; name=\"photo\"; filename=\"{os.path.basename(path)}\"\r\n"
        f"Content-Type: image/png\r\n\r\n".encode()
        + photo
        + b"\r\n"
    )
    parts.append(f"--{boundary}--\r\n".encode())
    body = b"".join(parts)
    url = f"https://api.telegram.org/bot{token()}/sendPhoto"
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    with _opener.open(req, timeout=120) as r:
        return json.loads(r.read())


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1].endswith(".png"):
        print(send_photo(sys.argv[1], "VibeGrade online ✅"))
    else:
        print(send_message("VibeGrade online ✅"))
