Write production-quality Python code for a Telegram/OG image card renderer using Pillow 12. Output ONE fenced python code block, no explanation.

FILE: bot/cards.py

Environment: Windows, Python 3.11, Pillow 12.3, no network. Fonts available at:
  BOLD   = "C:/Windows/Fonts/segoeuib.ttf"
  REG    = "C:/Windows/Fonts/segoeui.ttf"
  MONO   = "C:/Windows/Fonts/consolab.ttf"   (mono bold)
  MONO2  = "C:/Windows/Fonts/consola.ttf"

BRAND (the client's own design system — must be exact):
  BG        = (16, 18, 20)      #101214
  BG_CARD   = (22, 25, 28)
  ACCENT    = (223, 249, 2)     #dff902  (lime, used for the hero number + badge)
  TEXT      = (245, 245, 245)
  MUTED     = (138, 143, 152)
  LINE      = (38, 42, 47)

REQUIRED PUBLIC FUNCTIONS

1) render_graduation_card(data: dict, out_path: str) -> str
   Canvas 1200x630. Layout:
   - full bg BG, a 6px ACCENT vertical bar at x=0 (full height)
   - top-left: small caps label "VIBEGRADE" in MONO, MUTED, letterspaced
   - top-right: rounded pill with ACCENT fill and BG text "GRADUATED"
   - hero line (y~120): token SYMBOL in BOLD size ~96, TEXT colour, auto-shrink to fit 700px
   - under it: token NAME in REG 30, MUTED, truncated with "…" if too long
   - if data["image_path"] exists, load it, cover-crop to a 220x220 rounded square at right (x~900,y~110)
     else draw a 220x220 rounded square filled with BG_CARD and the first 2 chars of the symbol in ACCENT
   - middle row (y~300): three stat columns, value in MONO 44 TEXT, label in REG 20 MUTED:
        ("TIME TO GRAD", data["time_to_grad"]) , ("HOLDERS", data["holders"]) , ("VOLUME", data["volume"])
   - a big ACCENT rounded panel (x=60,y=430,w=1080,h=120) containing centered MONO 54 in BG:
        data["hero"]   e.g. "0.078 ETH TO GO"
   - footer (y~590): REG 20 MUTED left: data["footer_left"]; right-aligned MONO 20 MUTED: data["footer_right"]
   - thin 1px LINE separator above footer
   All text must be clipped so it never overflows the canvas. Use rounded_rectangle for panels/pills.

2) render_score_card(data: dict, out_path: str) -> str
   Canvas 1200x630, same brand. Layout:
   - bg BG, ACCENT 6px bar left
   - "VIBEGRADE · LAUNCH SCORE" small MONO MUTED top-left
   - huge score number data["score"] (0-100) centered-left at x~90,y~150: BOLD 220,
     colour = ACCENT if score>=75, (255,196,0) if >=50 else (255,92,92)
   - "/100" in MONO 56 MUTED right after it
   - token symbol + name stacked right of the score block
   - data["verdict"] in BOLD 40 TEXT under the score
   - up to 3 rows of data["notes"] (list of str), each with a small square bullet in ACCENT, REG 26 TEXT
   - bottom: data["footer"] in MONO 20 MUTED
   - optional data["breakdown"] dict of {label: 0-100}: draw 4 thin horizontal bars at the bottom
     (width proportional), ACCENT fill on LINE track, label in REG 18 MUTED

3) render_radar_card(rows: list[dict], out_path: str, title: str = "FINAL STRETCH") -> str
   Canvas 1200x800, brand. Title top-left BOLD 52, subtitle MONO 22 MUTED.
   Table of up to 8 rows: rank (MONO 30 ACCENT), symbol (BOLD 34), pair (REG 22 MUTED),
   progress bar (track LINE, fill ACCENT, height 8, width 260), pct (MONO 26),
   "to graduation" (MONO 26 TEXT right aligned). Row height 70 with 1px LINE separators.
   Each row model: {"symbol","name","pair","progress_bps":int,"to_grad":str,"is_native":bool}

RULES
- No PIL ImageDraw.textlength misuse: use draw.textlength(text, font=font) for measuring.
- Provide a helper fit_font(draw, text, path, max_size, max_width) that shrinks until it fits.
- rounded_rectangle needs radius <= half of the smaller side; guard it.
- Wrap everything in try/except so a bad image never crashes the caller; on error, log to stderr
  and still produce the card without the image.
- Type hints, docstrings, no globals other than the palette and font paths.
- End file with a __main__ block that renders a demo graduation card to /tmp/vg_demo.png (use os.environ TEMP on Windows fallback) so it can be smoke-tested.
- Only import: os, sys, math, io, PIL (Image, ImageDraw, ImageFont, ImageOps), typing.
