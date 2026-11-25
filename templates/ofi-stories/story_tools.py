"""Atlas open home story tools: OPEN tag renderer + story animator (split card or full-bleed).

  python3 story_tools.py tag "OPEN TODAY" "3:00 – 3:15PM" tag.png
  python3 story_tools.py animate split  card.png  out.mp4 --tag=tag.png [--anchor=topleft] p1.jpg p2.jpg p3.jpg
  python3 story_tools.py animate full   overlay.png out.mp4 --tag=tag.png [--tagpos=64,1556] p1.jpg p2.jpg p3.jpg

split: card.png is the full 1080x1920 card exported from Canva; photos animate in the top 1080x1040 panel.
full:  overlay.png is a 1080x1920 RGBA layer (gradients, icon, text) composited over full-frame photos.
Fakt Medium is fetched from atlas.com.au at runtime (licensed webfont: never commit the font file).
"""
import io, subprocess, sys, urllib.request
from PIL import Image, ImageDraw, ImageFont

FAKT_MEDIUM = "https://www.atlas.com.au/assets/FaktTT-Medium-DOHWa8E9.woff"  # check main CSS if renamed
TERRA = (0x73, 0x41, 0x37)
W, H = 1080, 1920
_font_bytes = None

def font(size):
    global _font_bytes
    if _font_bytes is None:
        _font_bytes = urllib.request.urlopen(FAKT_MEDIUM, timeout=30).read()
    return ImageFont.truetype(io.BytesIO(_font_bytes), size)

def _line(text, size=25, track=5.7, s=4):
    f = font(size * s)
    im = Image.new("L", (int(sum(f.getlength(c) for c in text) + (track * s + 2) * len(text) + 80 * s), size * s * 2))
    d, x = ImageDraw.Draw(im), 20 * s
    for c in text:
        d.text((x, size * s * 0.3), c, font=f, fill=255)
        x += f.getlength(c) + track * s
    im = im.crop(im.getbbox())
    return im.resize((round(im.width / s), round(im.height / s)), Image.LANCZOS)

def render_tag(line1, line2, pad=38, height=125, y1=32, y2=74, radius=4):
    """Matches the LNS OFI story tag: Terra box, Fakt Medium 25px, tracking 5.7px, centred caps."""
    a, b = _line(line1.upper()), _line(line2.upper())
    w = max(a.width, b.width) + 2 * pad
    tag = Image.new("RGBA", (w, height), (0, 0, 0, 0))
    ImageDraw.Draw(tag).rounded_rectangle((0, 0, w - 1, height - 1), radius=radius, fill=TERRA + (255,))
    for m, y in ((a, y1), (b, y2)):
        tag.paste(Image.new("RGBA", m.size, (255, 255, 255, 255)), ((w - m.width) // 2, y), m)
    return tag

def animate(mode, layer_path, out, photos, tag=None, tagpos=None, anchor="centre",
            fps=30, hold=4.5, xf=0.8, zoom=0.06):
    layer = Image.open(layer_path).convert("RGBA")
    assert layer.size == (W, H), layer.size
    ph = 1040 if mode == "split" else H
    tagpos = tagpos or ((64, 852) if mode == "split" else (64, 1556))
    imgs = [Image.open(p).convert("RGB") for p in photos]
    step = hold - xf
    total = step * (len(imgs) - 1) + hold

    def panel(img, t):
        sw, sh = img.size
        asp = W / ph
        bw, bh = (sh * asp, sh) if sw / sh > asp else (sw, sw / asp)
        z = 1 + zoom * min(max(t / hold, 0), 1)
        w, h = bw / z, bh / z
        x0, y0 = (0.0, 0.0) if anchor == "topleft" else ((sw - w) / 2, (sh - h) / 2)
        return img.resize((W, ph), Image.LANCZOS, box=(x0, y0, x0 + w, y0 + h))

    ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24",
                           "-s", f"{W}x{H}", "-r", str(fps), "-i", "-", "-c:v", "libx264", "-preset", "slow",
                           "-crf", "17", "-pix_fmt", "yuv420p", "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    for f in range(round(total * fps)):
        t = f / fps
        k = min(int(t // step), len(imgs) - 1)
        p = panel(imgs[k], t - k * step)
        if k > 0 and t < k * step + xf:
            p = Image.blend(panel(imgs[k - 1], t - (k - 1) * step), p, (t - k * step) / xf)
        if mode == "split":
            frame = layer.convert("RGB")
            frame.paste(p, (0, 0))
        else:
            frame = Image.alpha_composite(p.convert("RGBA"), layer).convert("RGB")
        if tag is not None:
            frame.paste(tag, tagpos, tag)
        ff.stdin.write(frame.tobytes())
    ff.stdin.close()
    if ff.wait():
        raise SystemExit("ffmpeg failed")

if __name__ == "__main__":
    a = sys.argv[1:]
    if a[0] == "tag":
        render_tag(a[1], a[2]).save(a[3])
    elif a[0] == "animate":
        mode, layer, out = a[1], a[2], a[3]
        opts = {k[2:]: v for k, v in (x.split("=", 1) for x in a[4:] if x.startswith("--"))}
        photos = [x for x in a[4:] if not x.startswith("--")]
        tag = Image.open(opts["tag"]).convert("RGBA") if "tag" in opts else None
        tp = tuple(int(v) for v in opts["tagpos"].split(",")) if "tagpos" in opts else None
        animate(mode, layer, out, photos, tag, tp, opts.get("anchor", "centre"))
