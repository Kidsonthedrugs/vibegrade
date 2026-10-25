PART 2 of bot/cards.py. Write ONLY the two new functions below, appended to an existing module that already defines:
    BG=(16,18,20)  CARD=(22,25,28)  ACCENT=(223,249,2)  TEXT=(245,245,245)  MUTED=(138,143,152)  LINE=(38,42,47)
    font(path,size) -> FreeTypeFont (lru_cached)
    text_w(draw,txt,f) -> float
    fit_font(draw,txt,path,max_size,max_width) -> FreeTypeFont
    ellipsize(draw,txt,f,max_width) -> str
    rounded_panel(img, box, fill, radius) -> None
    BOLD = "C:/Windows/Fonts/segoeuib.ttf"; REG = "C:/Windows/Fonts/segoeui.ttf";
    MONO = "C:/Windows/Fonts/consolab.ttf"; MONO_R = "C:/Windows/Fonts/consola.ttf"

Output ONE fenced python code block. No imports at the top needed except that you may assume
`from PIL import Image, ImageDraw, ImageFont` is already imported. Do NOT redefine helpers.

def render_score_card(data: dict, out_path: str) -> str
  Canvas 1200x630, fill BG, ACCENT bar x=0..6 full height.
  - "VIBEGRADE · LAUNCH SCORE" MONO 22 MUTED at (72,44), letter spacing not needed.
  - score = int(data.get("score",0)) clamped 0..100.
    Colon: draw score number with BOLD, start size 220, fit to max width 330, at (72,120) anchor "lt".
    Colour: ACCENT if >=75, (255,196,0) if >=50, else (255,92,92).
    Then "/100" in MONO 56 MUTED, baseline aligned to the bottom of the number, x = number right edge + 12.
  - Right of the score block (x=520): symbol in BOLD 64 TEXT (fit to 380), name in REG 28 MUTED
    ellipsized to 380, then data["verdict"] in BOLD 34 TEXT wrapped to max 3 lines of 56 chars each.
  - Under that (starts y=430): up to 3 items from data.get("notes", []) — each line: a 10x10
    ACCENT square bullet at x=72, text REG 26 TEXT at x=96, ellipsized to 1000. Row height 42.
  - data.get("breakdown") dict {label: 0..100}: if present draw up to 4 rows at the very bottom
    starting y=536: label REG 18 MUTED (width 240), track LINE rounded height 10 from x=300 to x=1000,
    fill ACCENT width proportional, value MONO 18 TEXT right aligned at x=1140.
  - footer: data.get("footer","vibegrade") MONO 20 MUTED at (72,600) anchor "ls".
  - return out_path.

def render_radar_card(rows: list[dict], out_path: str, title: str = "FINAL STRETCH") -> str
  Canvas 1200x800, fill BG, ACCENT bar x=0..6.
  - title BOLD 52 TEXT at (72,48); subtitle MONO 22 MUTED at (72,110) = data string passed in title's second line? No:
    subtitle is the fixed text "closest to graduation · vibegrade" .
  - header row at y=170: MONO 18 MUTED labels "#", "TOKEN", "PAIR", "PROGRESS", "TO GRAD"
    at x = 72, 130, 520, 700, 1000.
  - up to 8 rows, starting y=200, row height 70, 1px LINE separator at the bottom of each row.
    Each row: rank MONO 30 ACCENT at x=72; symbol BOLD 34 TEXT ellipsized to 300 at x=130;
    name REG 18 MUTED 4px under the symbol; pair REG 22 MUTED at x=520;
    progress track rounded rect (700, y+26)-(960, y+36) fill LINE with fill ACCENT of width
    int(260 * progress_bps/10000); pct MONO 24 TEXT at x=970;
    to_grad MONO 26 TEXT right aligned to x=1128 (use anchor "rt" or measure).
  - footer MONO 20 MUTED at (72,760) anchor "ls": "vibegrade · robinhood chain testnet".
  - rows may be empty: then draw REG 26 MUTED "no launches in range" centered.
  - return out_path.

Row keys: symbol, name, pair, progress_bps (int 0..10000), to_grad (str), is_native (bool, unused for layout).
Everything must be defensive with .get and str() so partial dicts never crash.
