#!/usr/bin/env python3
"""Make the 2:1 region thumbnails for the top of the OFI email.

Usage:
    python3 make_thumbs.py ../../ofi/14nov2026

Reads tile-lns.jpg, tile-sh.jpg and tile-byb.jpg from that folder, centre-crops
each to 2:1 and writes thumb-lns.jpg, thumb-sh.jpg and thumb-byb.jpg (288 x 144,
shown at 144 x 72 on desktop and 96 x 48 on mobile). Needs Pillow.
"""
import os, sys
from PIL import Image

W, H = 288, 144

folder = sys.argv[1]
for key in ("lns", "sh", "byb"):
    src = os.path.join(folder, f"tile-{key}.jpg")
    im = Image.open(src).convert("RGB")
    w, h = im.size
    if w / h > W / H:          # too wide: trim the sides
        cw, ch = round(h * W / H), h
    else:                      # too tall: trim top and bottom
        cw, ch = w, round(w * H / W)
    left, top = (w - cw) // 2, (h - ch) // 2
    out = im.crop((left, top, left + cw, top + ch)).resize((W, H), Image.LANCZOS)
    dst = os.path.join(folder, f"thumb-{key}.jpg")
    out.save(dst, "JPEG", quality=88, optimize=True, progressive=True)
    print("written", dst, out.size)
