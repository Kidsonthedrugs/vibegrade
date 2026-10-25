PART 3 of bot/cards.py. Existing module already defines: BG=(16,18,20) CARD=(22,25,28) ACCENT=(223,249,2) TEXT=(245,245,245) MUTED=(138,143,152) LINE=(38,42,47), font(path,size) cached, text_w(draw,txt,f), fit_font(draw,txt,path,max_size,max_width), ellipsize(draw,txt,f,max_width), rounded_panel(img,box,fill,radius), BOLD/REG/MONO font paths, and PIL Image/ImageDraw/ImageFont imported.

Write ONE function, one fenced python code block, no imports, no other functions:

def render_report_card(data: dict, out_path: str) -> str
  Canvas 1200x800, fill BG, ACCENT bar x=0..6 full height.
  - data["title"] BOLD 56 TEXT at (72,52) (ellipsized to 1000)
  - data["subtitle"] REG 24 MUTED at (72,122) (ellipsized to 1000)
  - data["stats"] is a list of up to 6 tuples (value_str, label_str). Lay them in a 2-column x 3-row grid
    beginning y=210: each cell is a rounded_panel box CARD radius 16, width 500, height 150,
    x = 72 for column 0 and 628 for column 1, gap 20 between rows.
    Inside each cell: value in MONO bold size 54 TEXT at (cell_x+28, cell_y+30),
    label in REG 20 MUTED at (cell_x+28, cell_y+104), both ellipsized to 440.
    If fewer than 6 stats, leave the remaining cells empty (do not draw them).
  - a thin LINE separator at y=700 from x=72 to x=1128
  - data.get("footer","vibegrade") MONO 20 MUTED at (72,730)
  - optionally data.get("note"): REG 22 TEXT at (72,660), ellipsized to 1000
  - return out_path
Defensive .get everywhere. No overlap with the footer.
