Write production-quality Python using PIL/Pillow 12. Output ONE fenced python code block, no explanation, no imports of anything except: os, sys, io, math, PIL (Image, ImageDraw, ImageFont, ImageOps), typing.

This is PART 1 of bot/cards.py — the helpers and the graduation card only.

Windows fonts:
  BOLD  = "C:/Windows/Fonts/segoeuib.ttf"
  REG   = "C:/Windows/Fonts/segoeui.ttf"
  MONO  = "C:/Windows/Fonts/consolab.ttf"
  MONO_R= "C:/Windows/Fonts/consola.ttf"

Palette (exact):
  BG = (16,18,20); CARD = (22,25,28); ACCENT = (223,249,2); TEXT = (245,245,245);
  MUTED = (138,143,152); LINE = (38,42,47)

Implement exactly these helpers:

def font(path: str, size: int) -> ImageFont.FreeTypeFont            # cached with functools.lru_cache
def text_w(draw, txt, f) -> float                                    # draw.textlength
def fit_font(draw, txt, path, max_size, max_width) -> ImageFont      # shrink by 2 until it fits, floor 8
def ellipsize(draw, txt, f, max_width) -> str                        # cut and append "…" if too wide
def cover_crop(img, w, h, radius) -> Image.Image                     # ImageOps.fit + rounded alpha mask
def rounded_panel(img, box, fill, radius)                            # draw rounded rect onto img
def pill(img, xy, text, f, fill, text_fill, pad_h=14, pad_v=8)       # rounded pill sized to text, returns box

def render_graduation_card(data: dict, out_path: str) -> str
  Canvas 1200x630, BG fill.
  - ACCENT vertical bar: x 0..6, full height.
  - x=60 left margin.
  - label "VIBEGRADE" MONO 22 MUTED at (60,40), letter-spaced by drawing with extra 3px gaps (simple loop).
  - right: pill "GRADUATED" with ACCENT fill, BG text, top-right at (1200-60-?, 34..66).
  - symbol: BOLD, start 100px, fit_font to max width 620, colour TEXT, at (60,110).
  - name: REG 30 MUTED ellipsized to 620 at (60, 110+symbol_height+6).
  - token art: 220x220 at right (x=1200-60-220=920, y=110). If data.get("image_path") and the file
    loads -> cover_crop(radius 28). Else rounded_panel CARD radius 28 + up to 2 chars of symbol
    centered in ACCENT BOLD 84.
  - stats row at y=380: three columns starting x=60, spacing 360. Each: value MONO 44 TEXT,
    label REG 20 MUTED 6px below. Values from data["time_to_grad"], data["holders"], data["volume"],
    labels "TIME TO GRAD", "HOLDERS", "VOLUME".
  - hero panel: rounded_panel box (60,470)-(1140,590) radius 20 fill ACCENT; centred text
    data["hero"] in MONO 54 BG (fit_font max width 1000).
  - separator LINE 1px at y=604 from x=60 to 1140.
  - footer baseline y=620: left REG 20 MUTED data["footer_left"]; right MONO 20 MUTED
    data["footer_right"] right-aligned to x=1140; both ellipsized to 500.
  - return out_path.

All string lookups must use .get with sensible defaults ("" or "—") so a partial dict cannot crash.
Wrap the image loading in try/except and fall back to the placeholder.
