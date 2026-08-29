#!/usr/bin/env python3
"""contact_sheet.py — 把多张封面拼成一张联系表，方便一次性肉眼检查。

用法: python3 contact_sheet.py out.png a.png b.png ...   (可加 --cols 3)
"""
import argparse
from PIL import Image

ap = argparse.ArgumentParser()
ap.add_argument("out")
ap.add_argument("images", nargs="+")
ap.add_argument("--cols", type=int, default=3)
ap.add_argument("--cell", type=int, default=440)
a = ap.parse_args()

cw = a.cell
ch = int(cw * 630 / 1200)
cols = a.cols
rows = (len(a.images) + cols - 1) // cols
pad = 10
sheet = Image.new("RGB", (cols * (cw + pad) + pad, rows * (ch + pad) + pad), "#F9F8F3")
for i, path in enumerate(a.images):
    im = Image.open(path).convert("RGB").resize((cw, ch), Image.LANCZOS)
    sheet.paste(im, (pad + (i % cols) * (cw + pad), pad + (i // cols) * (ch + pad)))
sheet.save(a.out)
print(a.out, sheet.size)
