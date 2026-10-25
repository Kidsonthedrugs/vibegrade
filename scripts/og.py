"""Render the 1200x630 social preview image (og.png)."""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from PIL import Image, ImageDraw  # noqa: E402

from bot.cards import ACCENT, BG, CARD, LINE, MUTED, TEXT, BOLD, MONO, REG, font, rounded_panel  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "og.png")


def main() -> int:
    W, H = 1200, 630
    img = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(img)

    # accent spine
    d.rectangle([0, 0, 8, H], fill=ACCENT)

    # brand
    d.text((72, 64), "vibegrade", font=font(BOLD, 34), fill=MUTED)

    d.text((72, 132), "Exact distance", font=font(BOLD, 92), fill=TEXT)
    d.text((72, 232), "to graduation.", font=font(BOLD, 92), fill=ACCENT)

    d.text((74, 356), "Every live vibe/vibe launch, measured", font=font(REG, 26), fill=MUTED)
    d.text((74, 394), "from the curve itself — verified to the wei.", font=font(REG, 26), fill=MUTED)

    # fake but representative sparkline, drawn with the brand accent
    panel_y = 470
    rounded_panel(img, (72, panel_y, 760, panel_y + 108), fill=CARD, radius=16)
    pts = [(96 + i * 52, panel_y + 84 - v) for i, v in enumerate([6, 14, 10, 26, 22, 40, 34, 56, 49, 68, 61, 80])]
    d.line(pts, fill=ACCENT, width=3, joint="curve")
    d.text((96, panel_y + 14), "FINAL STRETCH · 0.078 ETH TO GO", font=font(MONO, 18), fill=MUTED)

    # right card
    rounded_panel(img, (800, 132, 1128, 578), fill=CARD, radius=20)
    d.text((832, 164), "LAUNCH SCORE", font=font(MONO, 18), fill=MUTED)
    d.text((832, 200), "85", font=font(BOLD, 150), fill=ACCENT)
    d.text((1010, 300), "/100", font=font(MONO, 30), fill=MUTED)
    for i, (label, val) in enumerate([("tax fit", 100), ("weights", 90), ("airdrop", 100), ("pair", 100)]):
        y = 372 + i * 44
        d.text((832, y), label.upper(), font=font(REG, 16), fill=MUTED)
        rounded_panel(img, (940, y + 4, 1096, y + 12), fill=LINE, radius=4)
        rounded_panel(img, (940, y + 4, 940 + int(156 * val / 100), y + 12), fill=ACCENT, radius=4)

    d.text((72, 592), "vibegrade-eta.vercel.app", font=font(MONO, 22), fill=TEXT)
    d.text((1128, 592), "robinhood chain testnet", font=font(MONO, 18), fill=MUTED, anchor="ra")

    img.save(OUT)
    print("wrote", OUT, os.path.getsize(OUT), "bytes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
