#!/usr/bin/env python3
"""Generate the passport spread for the Republic of Kharvia.

An invented passport spread: data page (left) + visa/stamp page (right),
drawn with Pillow + DejaVu. Deterministic: no randomness, no network.
Writes entry.png (1024x1024) next to this file.
"""

import math
import os

from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = "/usr/share/fonts/truetype/dejavu"

INK = (31, 42, 68)          # navy document ink
INK_SOFT = (74, 88, 110)
PAPER = (243, 238, 225)     # warm passport paper
PAPER_DARK = (232, 225, 206)
DESK = (52, 57, 63)         # dark surface under the spread
RED = (140, 47, 47)         # stamp red-brown
BLUE = (38, 74, 122)        # stamp blue
GREEN = (46, 93, 75)        # visa green
PURPLE = (96, 62, 122)      # permit purple
GOLD = (146, 110, 44)


def font(name, size):
    return ImageFont.truetype(os.path.join(FONT_DIR, name), size)


SERIF = "DejaVuSerif.ttf"
SERIF_B = "DejaVuSerif-Bold.ttf"
SANS = "DejaVuSans.ttf"
SANS_B = "DejaVuSans-Bold.ttf"
MONO_B = "DejaVuSansMono-Bold.ttf"


# ---------------------------------------------------------------- MRZ (ICAO 9303)
def mrz_check(text):
    """MRZ check digit: values 0-9, A-Z=10-35, '<'=0; weights 7,3,1."""
    weights = (7, 3, 1)
    total = 0
    for i, ch in enumerate(text):
        if ch == "<":
            v = 0
        elif ch.isdigit():
            v = int(ch)
        else:
            v = ord(ch) - ord("A") + 10
        total += v * weights[i % 3]
    return str(total % 10)


def build_mrz():
    """Two 44-char TD3 lines for holder Mara Ilsen, passport KV-0417-8823."""
    line1 = "P<KHVILSEN<<MARA"
    line1 = line1 + "<" * (44 - len(line1))
    doc = "KV04178823"
    doc_c = mrz_check(doc)
    nat = "KHV"
    dob = "870614"           # 14 JUN 1987
    dob_c = mrz_check(dob)
    sex = "F"
    exp = "310312"           # 12 MAR 2031
    exp_c = mrz_check(exp)
    personal = "<" * 13           # TD3 positions 30-42 (13 chars)
    personal_c = mrz_check(personal)
    body = doc + doc_c + nat + dob + dob_c + sex + exp + exp_c + personal + personal_c
    line2 = body + mrz_check(body)
    assert len(line1) == 44 and len(line2) == 44, (len(line1), len(line2))
    return line1, line2


# ---------------------------------------------------------------- helpers
def rounded_page(draw, box, fill, outline, width=2):
    draw.rounded_rectangle(box, radius=10, fill=fill, outline=outline, width=width)


def guilloche(draw, box, color, step=22):
    """Faint wavy security lines across a page area."""
    x0, y0, x1, y1 = box
    for k in range(0, (y1 - y0) // step + 2):
        y_base = y0 + k * step
        pts = []
        for x in range(x0, x1 + 1, 8):
            y = y_base + 2 * math.sin((x - x0) / 34.0 + k * 0.7)
            pts.append((x, y))
        draw.line(pts, fill=color, width=1)


def text_center(draw, cx, y, s, fnt, fill=INK):
    w = draw.textlength(s, font=fnt)
    draw.text((cx - w / 2, y), s, font=fnt, fill=fill)


def text_right(draw, x, y, s, fnt, fill=INK):
    w = draw.textlength(s, font=fnt)
    draw.text((x - w, y), s, font=fnt, fill=fill)


def draw_emblem(draw, cx, cy, r, ink=INK, fill_bg=None):
    """Coat of arms of Kharvia: ibex on three peaks inside a double ring."""
    if fill_bg is not None:
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=fill_bg)
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], outline=ink, width=3)
    draw.ellipse([cx - r + 5, cy - r + 5, cx + r - 5, cy + r - 5],
                 outline=ink, width=1)
    # three peaks
    base = cy + r * 0.55
    peaks = [(-0.62, 0.30), (0.0, -0.05), (0.62, 0.30)]
    for px, py in peaks:
        x = cx + px * r
        y = cy + py * r
        draw.polygon([(x - r * 0.30, base), (x, y), (x + r * 0.30, base)],
                     fill=ink)
    # ibex: body, head, horns, legs, tail
    bx, by = cx, cy - r * 0.12
    draw.ellipse([bx - r * 0.30, by - r * 0.10, bx + r * 0.30, by + r * 0.12],
                 fill=ink)
    draw.ellipse([bx + r * 0.24, by - r * 0.22, bx + r * 0.42, by - r * 0.02],
                 fill=ink)
    # horns: two arcs sweeping back
    draw.arc([bx + r * 0.18, by - r * 0.52, bx + r * 0.62, by - r * 0.10],
             start=200, end=330, fill=ink, width=3)
    draw.arc([bx + r * 0.10, by - r * 0.48, bx + r * 0.54, by - r * 0.06],
             start=200, end=330, fill=ink, width=3)
    # legs
    for lx in (-0.20, -0.07, 0.10, 0.22):
        draw.line([(bx + lx * r, by + r * 0.10),
                   (bx + lx * r, base - 1)], fill=ink, width=3)
    # tail
    draw.line([(bx - r * 0.30, by - r * 0.02),
               (bx - r * 0.42, by - r * 0.14)], fill=ink, width=3)


def draw_portrait(draw, box):
    """Engraved-style headshot of Mara Ilsen, 34, dark braided hair."""
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    # photo background: soft blue-grey with halftone dots
    draw.rectangle(box, fill=(196, 206, 214))
    for gy in range(y0 + 6, y1, 9):
        for gx in range(x0 + 6, x1, 9):
            draw.ellipse([gx - 1, gy - 1, gx + 1, gy + 1],
                         fill=(178, 190, 200))
    cx = x0 + w // 2
    # shoulders / high-collared coat
    draw.polygon([(x0 + 8, y1), (x0 + 34, y0 + h * 0.74),
                  (cx - 12, y0 + h * 0.66), (cx + 12, y0 + h * 0.66),
                  (x0 + w - 34, y0 + h * 0.74), (x1 - 8, y1)],
                 fill=(43, 58, 85))
    # shirt V at the neck
    draw.polygon([(cx - 13, y0 + h * 0.68), (cx, y0 + h * 0.82),
                  (cx + 13, y0 + h * 0.68)], fill=(238, 236, 228))
    # collar
    draw.polygon([(cx - 26, y0 + h * 0.66), (cx, y0 + h * 0.80),
                  (cx - 8, y0 + h * 0.66)], fill=(30, 40, 60))
    draw.polygon([(cx + 26, y0 + h * 0.66), (cx, y0 + h * 0.80),
                  (cx + 8, y0 + h * 0.66)], fill=(30, 40, 60))
    # neck
    draw.rectangle([cx - 11, y0 + h * 0.56, cx + 11, y0 + h * 0.68],
                   fill=(217, 180, 143))
    # face
    fx0, fy0 = cx - 26, y0 + h * 0.14
    fx1, fy1 = cx + 26, y0 + h * 0.60
    draw.ellipse([fx0, fy0, fx1, fy1], fill=(217, 180, 143))
    # soft shading on one side of the face
    draw.ellipse([fx0 + 22, fy0 + 8, fx1 + 2, fy1 - 6], fill=(206, 168, 130))
    # hair: cap over the top of the head, parted in the middle
    draw.pieslice([fx0 - 4, fy0 - 12, fx1 + 4, fy0 + 46],
                  start=180, end=360, fill=(58, 42, 32))
    draw.polygon([(fx0 - 2, fy0 + 26), (fx0 + 4, fy0 - 6),
                  (cx - 3, fy0 + 30), (cx, fy0 + 8),
                  (cx + 3, fy0 + 30), (fx1 - 4, fy0 - 6),
                  (fx1 + 2, fy0 + 26), (fx1 + 2, fy0 + 44),
                  (fx0 - 2, fy0 + 44)], fill=(58, 42, 32))
    # braid over the right shoulder
    bx = x0 + w - 30
    by = y0 + h * 0.42
    for i in range(6):
        yy = by + i * 13
        rr = 8 - i
        draw.ellipse([bx - rr, yy - 7, bx + rr, yy + 7], fill=(58, 42, 32))
        draw.ellipse([bx - rr + 3, yy - 7, bx + rr - 2, yy + 7],
                     fill=(74, 56, 44))
    # brows, eyes, nose, lips
    ey = y0 + h * 0.34
    for sgn in (-1, 1):
        ex = cx + sgn * 13
        draw.arc([ex - 8, ey - 6, ex + 8, ey + 2], start=200, end=340,
                 fill=(58, 42, 32), width=2)
        draw.ellipse([ex - 5, ey + 2, ex + 5, ey + 7], fill=(250, 248, 242))
        draw.ellipse([ex - 2, ey + 3, ex + 2, ey + 7], fill=(40, 32, 28))
    # nose
    draw.line([(cx, y0 + h * 0.38), (cx - 2, y0 + h * 0.48),
               (cx + 3, y0 + h * 0.50)], fill=(170, 128, 96), width=2)
    # lips
    ly = y0 + h * 0.545
    draw.arc([cx - 8, ly - 3, cx + 8, ly + 4], start=0, end=180,
             fill=(158, 96, 88), width=2)
    draw.line([(cx - 8, ly + 1), (cx + 8, ly + 1)], fill=(158, 96, 88),
              width=1)
    # (no hatch over the face: it reads as scratches at this size)
    # photo border
    draw.rectangle(box, outline=INK, width=2)


# ---------------------------------------------------------------- data page
def draw_data_page(draw, x0, y0, w, h):
    """Left page: the holder's data page."""
    x1, y1 = x0 + w, y0 + h
    rounded_page(draw, [x0, y0, x1, y1], PAPER, INK)
    guilloche(draw, [x0 + 10, y0 + 10, x1 - 10, y1 - 10], (229, 222, 206))
    # header: emblem + country name
    draw_emblem(draw, x0 + w // 2, y0 + 52, 34)
    text_center(draw, x0 + w // 2, y0 + 96, "REPUBLIC OF KHARVIA",
                font(SERIF_B, 21))
    text_center(draw, x0 + w // 2, y0 + 122, "ХАРВИЯ",
                font(SERIF, 15), fill=INK_SOFT)
    # double rule
    draw.line([(x0 + 30, y0 + 152), (x1 - 30, y0 + 152)], fill=INK, width=2)
    draw.line([(x0 + 30, y0 + 156), (x1 - 30, y0 + 156)], fill=INK, width=1)
    text_center(draw, x0 + w // 2, y0 + 164, "P A S S P O R T",
                font(SERIF_B, 15))
    text_center(draw, x0 + w // 2, y0 + 186, "ПАСПОРТ",
                font(SERIF, 11), fill=INK_SOFT)
    text_center(draw, x0 + w // 2, y0 + 206,
                "Type  P        Code  KHV        No.  KV-0417-8823",
                font(SANS, 12))
    # photo
    photo = [x0 + 24, y0 + 238, x0 + 154, y0 + 403]
    draw_portrait(draw, photo)
    # circular office seal overlapping the photo's lower right corner
    sx, sy, sr = x0 + 138, y0 + 388, 26
    draw.ellipse([sx - sr, sy - sr, sx + sr, sy + sr],
                 outline=BLUE, width=2)
    draw.ellipse([sx - sr + 5, sy - sr + 5, sx + sr - 5, sy + sr - 5],
                 outline=BLUE, width=1)
    text_center(draw, sx, sy - 14, "TARNAK", font(SANS_B, 8), fill=BLUE)
    text_center(draw, sx, sy - 4, "PASSPORT", font(SANS_B, 7), fill=BLUE)
    text_center(draw, sx, sy + 5, "OFFICE", font(SANS_B, 7), fill=BLUE)
    draw.ellipse([sx - 3, sy + 13, sx + 3, sy + 17], fill=BLUE)
    # data fields, right of the photo
    fx = x0 + 172
    fields = [
        ("Surname / Фамилия", "ILSEN  /  ИЛЬСЕН"),
        ("Given names / Имя", "MARA  /  МАРА"),
        ("Nationality / Гражданство", "KHARVIAN"),
        ("Date of birth / Дата рождения", "14 JUN 1987"),
        ("Place of birth / Место рождения", "TARNAK"),
        ("Sex / Пол", "F"),
        ("Date of issue / Дата выдачи", "12 MAR 2021"),
        ("Date of expiry / Срок действия", "12 MAR 2031"),
        ("Authority / Орган", "MINISTRY OF THE INTERIOR"),
        ("", "TARNAK"),
    ]
    yy = y0 + 238
    for label, value in fields:
        if label:
            draw.text((fx, yy), label, font=font(SANS, 9), fill=INK_SOFT)
            draw.text((fx, yy + 11), value, font=font(SERIF_B, 13), fill=INK)
            yy += 30
        else:
            draw.text((fx, yy), value, font=font(SERIF_B, 13), fill=INK)
            yy += 19
    # signature, below the fields
    sy = y0 + 540
    draw.text((x0 + 24, sy), "Holder's signature / Подпись",
              font=font(SANS, 9), fill=INK_SOFT)
    pts = []
    for i in range(90):
        t = i / 89.0
        px = x0 + 24 + t * 150
        py = sy + 30 + 5 * math.sin(t * 21.0) * (1 - t * 0.4) \
            - 6 * math.sin(t * 6.0)
        pts.append((px, py))
    draw.line(pts, fill=(28, 44, 92), width=2)
    draw.line([(x0 + 24, sy + 44), (x0 + 174, sy + 44)], fill=INK_SOFT,
              width=1)
    # small print above the MRZ
    draw.line([(x0 + 24, y0 + 606), (x1 - 24, y0 + 606)], fill=INK, width=1)
    draw.text((x0 + 24, y0 + 614),
              "This passport is the property of the Republic of Kharvia.",
              font=font(SANS, 9), fill=INK_SOFT)
    # machine-readable zone
    line1, line2 = build_mrz()
    draw.text((x0 + 24, y0 + 638), line1, font=font(MONO_B, 15), fill=INK)
    draw.text((x0 + 24, y0 + 662), line2, font=font(MONO_B, 15), fill=INK)
    # page number
    text_right(draw, x1 - 24, y1 - 30, "3", font(SANS, 11), fill=INK_SOFT)


# ---------------------------------------------------------------- stamp helpers
def make_stamp(w, h, border_fn, lines, fnt, color, angle):
    """Draw a stamp (border + text) on its own layer, then rotate it."""
    pad = 24
    layer = Image.new("RGBA", (w + 2 * pad, h + 2 * pad), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    border_fn(d, pad, pad, w, h)
    stamp_text(d, pad + w // 2, pad + h // 2, lines, fnt, color)
    return layer.rotate(angle, resample=Image.BICUBIC, expand=False)


def paste_stamp(img, layer, x, y):
    img.alpha_composite(layer, (x - 24, y - 24))


def oval_stamp_lines(color):
    def fn(d, x, y, w, h):
        d.ellipse([x, y, x + w, y + h], outline=color, width=3)
        d.ellipse([x + 5, y + 5, x + w - 5, y + h - 5], outline=color,
                  width=1)
    return fn


def rect_stamp_lines(color):
    def fn(d, x, y, w, h):
        d.rectangle([x, y, x + w, y + h], outline=color, width=3)
        d.rectangle([x + 5, y + 5, x + w - 5, y + h - 5], outline=color,
                    width=1)
    return fn


def round_stamp_lines(color):
    def fn(d, x, y, w, h):
        r = min(w, h)
        cx, cy = x + w // 2, y + h // 2
        d.ellipse([cx - r // 2, cy - r // 2, cx + r // 2, cy + r // 2],
                  outline=color, width=3)
        d.ellipse([cx - r // 2 + 5, cy - r // 2 + 5,
                   cx + r // 2 - 5, cy + r // 2 - 5],
                  outline=color, width=1)
    return fn


def stamp_text(d, cx, cy, lines, fnt, color):
    """Center a stack of text lines inside a stamp layer."""
    total = len(lines) * 13
    yy = cy - total // 2
    for s in lines:
        w = d.textlength(s, font=fnt)
        d.text((cx - w / 2, yy), s, font=fnt, fill=color)
        yy += 13


# ---------------------------------------------------------------- visa page
def draw_visa_page(img, draw, x0, y0, w, h):
    """Right page: visa sticker, entry/exit stamps, observatory permit."""
    x1, y1 = x0 + w, y0 + h
    rounded_page(draw, [x0, y0, x1, y1], PAPER, INK)
    guilloche(draw, [x0 + 10, y0 + 10, x1 - 10, y1 - 10], (229, 222, 206))
    # faint watermark emblem in the middle of the page
    wm = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    wd = ImageDraw.Draw(wm)
    draw_emblem(wd, w // 2, h // 2 + 40, 150, ink=(31, 42, 68, 22))
    img.alpha_composite(wm, (x0, y0))
    # header
    draw.text((x0 + 24, y0 + 22), "VISAS", font=font(SERIF_B, 16), fill=INK)
    text_right(draw, x1 - 24, y0 + 22, "ВИЗЫ", font(SERIF, 13),
               fill=INK_SOFT)
    draw.line([(x0 + 24, y0 + 50), (x1 - 24, y0 + 50)], fill=INK, width=2)
    # ---- Suthal visa sticker
    vx, vy, vw, vh = x0 + 24, y0 + 66, w - 48, 150
    draw.rectangle([vx, vy, vx + vw, vy + vh], fill=(224, 236, 226),
                   outline=GREEN, width=2)
    draw.rectangle([vx + 5, vy + 5, vx + vw - 5, vy + vh - 5],
                   outline=GREEN, width=1)
    draw.text((vx + 14, vy + 10), "VISA", font=font(SERIF_B, 15),
              fill=GREEN)
    draw.text((vx + 66, vy + 12), "REPUBLIC OF SUTHAL",
              font=font(SERIF_B, 13), fill=GREEN)
    text_right(draw, vx + vw - 14, vy + 12, "No. VS-2291-447",
               font(SANS, 10), fill=GREEN)
    draw.line([(vx + 14, vy + 36), (vx + vw - 14, vy + 36)], fill=GREEN,
              width=1)
    visa_rows = [
        ("Type", "C  —  30 DAYS  —  SINGLE ENTRY"),
        ("Issued", "28 SEP 2023   at Consulate of Suthal, Tarnak"),
        ("Valid until", "27 NOV 2023"),
        ("Holder", "ILSEN, MARA  —  KV-0417-8823"),
    ]
    yy = vy + 44
    for label, value in visa_rows:
        draw.text((vx + 14, yy), label, font=font(SANS_B, 10), fill=GREEN)
        draw.text((vx + 104, yy), value, font=font(SANS, 10), fill=INK)
        yy += 22
    draw.text((vx + 14, vy + vh - 22),
              "Good for one entry by sea or land. Keep with passport.",
              font=font(SANS, 9), fill=INK_SOFT)
    # fee stamp overlapping the visa sticker's corner
    fee = make_stamp(140, 56, rect_stamp_lines(RED),
                     ["FEE 40 TALM", "PAID"], font(SANS_B, 10), RED, -10)
    paste_stamp(img, fee, vx + vw - 138, vy + vh - 34)
    # ---- travel stamps, chronological, all after the 12 MAR 2021 issue
    small = font(SANS_B, 9)
    # Drazhyn pair, oval, blue
    for (sx, title, date, ang) in [
            (x0 + 24, "ARRIVAL", "02 APR 2021", -4),
            (x0 + 236, "DEPARTURE", "09 APR 2021", 5)]:
        lay = make_stamp(188, 88, oval_stamp_lines(BLUE),
                         ["DRAZHYN", title, "PORT OF VELEZ", date],
                         small, BLUE, ang)
        paste_stamp(img, lay, sx, y0 + 240)
    # Ostrovek pair, rectangle, red-brown
    for (sx, title, date, ang) in [
            (x0 + 24, "ARRIVAL", "21 JUN 2022", 4),
            (x0 + 236, "DEPARTURE", "30 JUN 2022", -5)]:
        lay = make_stamp(188, 88, rect_stamp_lines(RED),
                         ["OSTROVEK", title, "KAMEN BRIDGE", date],
                         small, RED, ang)
        paste_stamp(img, lay, sx, y0 + 344)
    # Suthal pair, round, green
    for (sx, title, date, ang) in [
            (x0 + 24, "ARRIVAL", "15 OCT 2023", -6),
            (x0 + 236, "DEPARTURE", "02 NOV 2023", 6)]:
        lay = make_stamp(188, 88, round_stamp_lines(GREEN),
                         ["SUTHAL", title, "PORT OF LIR", date],
                         small, GREEN, ang)
        paste_stamp(img, lay, sx, y0 + 448)
    # Mt. Orun Observatory night-visitor permit, purple
    lay = make_stamp(280, 60, rect_stamp_lines(PURPLE),
                     ["MT. ORUN OBSERVATORY — NIGHT VISITOR PERMIT",
                      "18 AUG 2022  •  VALID 7 DAYS"],
                     font(SANS_B, 9), PURPLE, -4)
    paste_stamp(img, lay, x0 + 86, y0 + 566)
    # footer
    draw.text((x0 + 24, y1 - 34),
              "Kharvia — Ministry of the Interior",
              font=font(SANS, 9), fill=INK_SOFT)
    text_right(draw, x1 - 24, y1 - 30, "12", font(SANS, 11), fill=INK_SOFT)


# ---------------------------------------------------------------- render
def main():
    img = Image.new("RGBA", (1024, 1024), DESK + (255,))
    draw = ImageDraw.Draw(img)
    # soft shadow under the open spread
    draw.rounded_rectangle([56, 168, 984, 884], radius=12,
                           fill=(28, 31, 35, 255))
    draw_data_page(draw, 48, 152, 452, 720)
    draw_visa_page(img, draw, 524, 152, 452, 720)
    out = os.path.join(HERE, "entry.png")
    img.convert("RGB").save(out, format="PNG")
    print("wrote", out, os.path.getsize(out), "bytes")


if __name__ == "__main__":
    main()
