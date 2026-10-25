import os
import math
from functools import lru_cache
from typing import Tuple
from PIL import Image, ImageDraw, ImageFont, ImageOps

BOLD = "C:/Windows/Fonts/segoeuib.ttf"
REG = "C:/Windows/Fonts/segoeui.ttf"
MONO = "C:/Windows/Fonts/consolab.ttf"
MONO_R = "C:/Windows/Fonts/consola.ttf"

BG = (16, 18, 20)
CARD = (22, 25, 28)
ACCENT = (223, 249, 2)
TEXT = (245, 245, 245)
MUTED = (138, 143, 152)
LINE = (38, 42, 47)


@lru_cache(maxsize=None)
def font(path: str, size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(path, size)


def text_w(draw: ImageDraw.ImageDraw, txt: str, f: ImageFont.FreeTypeFont) -> float:
    return draw.textlength(txt, font=f)


def fit_font(
    draw: ImageDraw.ImageDraw,
    txt: str,
    path: str,
    max_size: int,
    max_width: float,
) -> ImageFont.FreeTypeFont:
    size = max_size
    while size >= 8:
        f = font(path, size)
        if text_w(draw, txt, f) <= max_width:
            return f
        size -= 2
    return font(path, 8)


def ellipsize(
    draw: ImageDraw.ImageDraw,
    txt: str,
    f: ImageFont.FreeTypeFont,
    max_width: float,
) -> str:
    if text_w(draw, txt, f) <= max_width:
        return txt
    ellipsis = "…"
    while txt and text_w(draw, txt + ellipsis, f) > max_width:
        txt = txt[:-1]
    return txt + ellipsis


def cover_crop(img: Image.Image, w: int, h: int, radius: int) -> Image.Image:
    fitted = ImageOps.fit(img, (w, h), method=Image.LANCZOS, centering=(0.5, 0.5))
    mask = Image.new("L", (w, h), 0)
    mask_draw = ImageDraw.Draw(mask)
    mask_draw.rounded_rectangle((0, 0, w, h), radius=radius, fill=255)
    result = fitted.convert("RGBA")
    result.putalpha(mask)
    return result


def rounded_panel(
    img: Image.Image,
    box: Tuple[int, int, int, int],
    fill: Tuple[int, int, int],
    radius: int,
) -> None:
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle(box, radius=radius, fill=fill)


def pill(
    img: Image.Image,
    xy: Tuple[int, int],
    text: str,
    f: ImageFont.FreeTypeFont,
    fill: Tuple[int, int, int],
    text_fill: Tuple[int, int, int],
    pad_h: int = 14,
    pad_v: int = 8,
) -> Tuple[int, int, int, int]:
    draw = ImageDraw.Draw(img)
    bbox = f.getbbox(text)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    x, y = xy
    box = (x, y, x + tw + pad_h * 2, y + th + pad_v * 2)
    rounded_panel(img, box, fill, radius=(box[3] - box[1]) // 2)
    draw.text((x + pad_h, y + pad_v - bbox[1]), text, font=f, fill=text_fill)
    return box


def render_graduation_card(data: dict, out_path: str) -> str:
    img = Image.new("RGB", (1200, 630), BG)
    draw = ImageDraw.Draw(img)

    draw.rectangle((0, 0, 6, 630), fill=ACCENT)

    label = "VIBEGRADE"
    f_label = font(MONO, 22)
    x = 60
    for ch in label:
        draw.text((x, 40), ch, font=f_label, fill=MUTED)
        x += int(text_w(draw, ch, f_label)) + 3

    f_pill = font(MONO, 22)
    pill_text = "GRADUATED"
    pill_bbox = f_pill.getbbox(pill_text)
    pill_w = (pill_bbox[2] - pill_bbox[0]) + 14 * 2
    pill(img, (1140 - pill_w, 34), pill_text, f_pill, ACCENT, BG, pad_h=14, pad_v=8)

    symbol = data.get("symbol", "")
    f_symbol = fit_font(draw, symbol, BOLD, 100, 620)
    draw.text((60, 110), symbol, font=f_symbol, fill=TEXT)
    symbol_h = int(f_symbol.size * 1.02)

    name = data.get("name", "")
    f_name = font(REG, 30)
    name_text = ellipsize(draw, name, f_name, 620)
    draw.text((60, 110 + symbol_h + 8), name_text, font=f_name, fill=MUTED)

    art_x, art_y = 920, 110
    loaded = False
    image_path = data.get("image_path")
    if image_path:
        try:
            with Image.open(image_path) as art_img:
                art = cover_crop(art_img, 220, 220, 28)
                img.paste(art, (art_x, art_y), art)
                loaded = True
        except Exception:
            loaded = False
    if not loaded:
        rounded_panel(img, (art_x, art_y, art_x + 220, art_y + 220), CARD, 28)
        chars = symbol[:2]
        if chars:
            f_art = font(BOLD, 84)
            draw.text((art_x + 110, art_y + 110), chars, font=f_art, fill=ACCENT, anchor="mm")

    f_value = font(MONO, 44)
    f_stat_label = font(REG, 20)
    stats = [
        ("time_to_grad", "TIME TO GRAD"),
        ("holders", "HOLDERS"),
        ("volume", "VOLUME"),
    ]
    for i, (key, lbl) in enumerate(stats):
        col_x = 60 + i * 360
        val = ellipsize(draw, str(data.get(key, "—")), f_value, 320)
        draw.text((col_x, 380), val, font=f_value, fill=TEXT)
        value_bbox = f_value.getbbox(val)
        value_h = value_bbox[3] - value_bbox[1] if value_bbox else 44
        draw.text((col_x, 380 + value_h + 6), lbl, font=f_stat_label, fill=MUTED)

    rounded_panel(img, (60, 470, 1140, 590), ACCENT, 20)
    hero = data.get("hero", "")
    f_hero = fit_font(draw, hero, MONO, 54, 1000)
    hero_bbox = f_hero.getbbox(hero) if hero else (0, 0, 0, 0)
    hero_w = hero_bbox[2] - hero_bbox[0]
    hero_h = hero_bbox[3] - hero_bbox[1]
    hero_x = 60 + (1080 - hero_w) // 2
    hero_y = 470 + (120 - hero_h) // 2
    draw.text((hero_x, hero_y), hero, font=f_hero, fill=BG)

    draw.line([(60, 604), (1140, 604)], fill=LINE, width=1)

    f_footer_reg = font(REG, 20)
    f_footer_mono = font(MONO, 20)
    footer_left = ellipsize(draw, data.get("footer_left", ""), f_footer_reg, 500)
    footer_right = ellipsize(draw, data.get("footer_right", ""), f_footer_mono, 500)
    draw.text((60, 620), footer_left, font=f_footer_reg, fill=MUTED, anchor="ls")
    draw.text((1140, 620), footer_right, font=f_footer_mono, fill=MUTED, anchor="rs")

    img.save(out_path)
    return out_path


def _wrap_px(draw, text, f, max_w, max_lines=3):
    """Pixel-accurate word wrap; the last line is ellipsized."""
    words = str(text).split()
    if not words:
        return []
    lines, cur = [], ""
    for w in words:
        cand = (cur + " " + w) if cur else w
        if text_w(draw, cand, f) <= max_w or not cur:
            cur = cand
        else:
            lines.append(cur)
            cur = w
            if len(lines) == max_lines:
                break
    if cur and len(lines) < max_lines:
        lines.append(cur)
    if len(lines) == max_lines and text_w(draw, lines[-1], f) > max_w:
        lines[-1] = ellipsize(draw, lines[-1], f, max_w)
    return lines[:max_lines]


def render_score_card(data: dict, out_path: str) -> str:
    w, h = 1200, 630
    img = Image.new("RGB", (w, h), BG)
    draw = ImageDraw.Draw(img)
    draw.rectangle([0, 0, 6, h], fill=ACCENT)

    draw.text((72, 40), "VIBEGRADE · LAUNCH SCORE", font=font(MONO, 22), fill=MUTED)

    try:
        score = max(0, min(100, int(data.get("score", 0))))
    except Exception:
        score = 0
    score_color = ACCENT if score >= 75 else ((255, 196, 0) if score >= 50 else (255, 92, 92))

    score_str = str(score)
    score_font = fit_font(draw, score_str, BOLD, 200, 300)
    draw.text((72, 108), score_str, font=score_font, fill=score_color)
    sb = draw.textbbox((72, 108), score_str, font=score_font)
    draw.text((sb[2] + 14, sb[3]), "/100", font=font(MONO, 48), fill=MUTED, anchor="ls")

    draw.line([(470, 120), (470, 360)], fill=LINE, width=1)

    x = 510
    symbol = str(data.get("symbol", ""))
    sym_font = fit_font(draw, symbol, BOLD, 60, 600)
    draw.text((x, 108), symbol, font=sym_font, fill=TEXT)
    name_y = 108 + int(sym_font.size * 1.05)
    draw.text((x, name_y), ellipsize(draw, str(data.get("name", "")), font(REG, 26), 600),
              font=font(REG, 26), fill=MUTED)

    verdict = str(data.get("verdict", ""))
    if verdict:
        vf = font(BOLD, 30)
        vy = name_y + 56
        for line in _wrap_px(draw, verdict, vf, 600, 3):
            draw.text((x, vy), line, font=vf, fill=TEXT)
            vy += 40

    notes = data.get("notes") or []
    if not isinstance(notes, (list, tuple)):
        notes = []
    nf = font(REG, 23)
    ny = 340
    for note in notes[:3]:
        draw.rectangle([72, ny + 8, 82, ny + 18], fill=ACCENT)
        draw.text((98, ny), ellipsize(draw, str(note), nf, 1010), font=nf, fill=TEXT)
        ny += 40

    breakdown = data.get("breakdown")
    if isinstance(breakdown, dict) and breakdown:
        lf, vf2 = font(REG, 15), font(MONO, 15)
        y = 470
        for label, value in list(breakdown.items())[:6]:
            draw.text((72, y), ellipsize(draw, str(label).upper(), lf, 210), font=lf, fill=MUTED)
            try:
                val = max(0.0, min(100.0, float(value)))
            except Exception:
                val = 0.0
            rounded_panel(img, (300, y + 1, 1040, y + 8), fill=LINE, radius=4)
            fill_w = max(2, int(740 * val / 100))
            rounded_panel(img, (300, y + 1, 300 + fill_w, y + 8), fill=ACCENT, radius=4)
            draw.text((1130, y - 1), str(int(round(val))), font=vf2, fill=TEXT, anchor="ra")
            y += 25

    img.save(out_path)
    return out_path


def render_radar_card(rows: list[dict], out_path: str,
                      title: str = "FINAL STRETCH") -> str:
    w, h = 1200, 800
    img = Image.new("RGB", (w, h), BG)
    draw = ImageDraw.Draw(img)

    draw.rectangle([0, 0, 6, h], fill=ACCENT)

    draw.text((72, 48), title, font=font(BOLD, 52),
              fill=TEXT, anchor="lt")
    draw.text((72, 110), "closest to graduation · vibegrade",
              font=font(MONO, 22), fill=MUTED, anchor="lt")

    header_font = font(MONO, 18)
    headers = [("#", 72), ("TOKEN", 130), ("PAIR", 470),
               ("PROGRESS", 620), ("TO GRAD", 962)]
    for text, x in headers:
        draw.text((x, 170), text, font=header_font,
                  fill=MUTED, anchor="lt")

    if not rows:
        draw.text((w // 2, h // 2), "no launches in range",
                  font=font(REG, 26), fill=MUTED, anchor="mm")
    else:
        for idx, row in enumerate(rows[:8]):
            y = 200 + idx * 70

            draw.line([(72, y + 70), (1128, y + 70)],
                      fill=LINE, width=1)

            rank = str(idx + 1)
            draw.text((72, y + 35), rank, font=font(MONO, 30),
                      fill=ACCENT, anchor="lm")

            symbol = str(row.get("symbol", ""))
            name = str(row.get("name", ""))
            pair = str(row.get("pair", ""))

            sym_font = fit_font(draw, symbol, BOLD, 34, 300)
            sym_text = ellipsize(draw, symbol, sym_font, 300)
            draw.text((130, y + 12), sym_text, font=sym_font,
                      fill=TEXT, anchor="lt")
            sym_bbox = draw.textbbox((130, y + 12), sym_text,
                                     font=sym_font, anchor="lt")

            name_font = font(REG, 18)
            name_text = ellipsize(draw, name, name_font, 300)
            draw.text((130, sym_bbox[3] + 4), name_text,
                      font=name_font, fill=MUTED, anchor="lt")

            pair_font = font(REG, 22)
            pair_text = ellipsize(draw, pair, pair_font, 130)
            draw.text((470, y + 35), pair_text, font=pair_font,
                      fill=MUTED, anchor="lm")

            try:
                progress_bps = int(row.get("progress_bps", 0) or 0)
            except Exception:
                progress_bps = 0
            progress_bps = max(0, min(10000, progress_bps))

            rounded_panel(img, (620, y + 26, 860, y + 36),
                          fill=LINE, radius=5)
            fill_width = int(240 * progress_bps / 10000)
            if fill_width >= 2:
                rounded_panel(img,
                              (620, y + 26, 620 + fill_width, y + 36),
                              fill=ACCENT, radius=5)

            pct = f"{progress_bps / 100:.2f}%"
            draw.text((872, y + 35), pct, font=font(MONO, 22),
                      fill=MUTED, anchor="lm")

            to_grad = str(row.get("to_grad", ""))
            f_grad = font(MONO, 24)
            to_grad = ellipsize(draw, to_grad, f_grad, 165)
            draw.text((1130, y + 35), to_grad, font=f_grad,
                      fill=TEXT, anchor="rm")

    draw.text((72, 760), "vibegrade · robinhood chain testnet",
              font=font(MONO, 20), fill=MUTED, anchor="ls")

    img.save(out_path)
    return out_path
