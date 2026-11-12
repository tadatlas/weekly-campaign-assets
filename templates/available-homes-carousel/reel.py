"""One continuous video from a carousel job: the cover footage, then each card's photo full bleed with a slow
push-in, dissolving into the next while the address and details swap (old words out, then new words in).

    python3 reel.py jobs/<job>.json post      # 1080 x 1350, for an Instagram video post
    python3 reel.py jobs/<job>.json story     # 1080 x 1920, for an Instagram story
    python3 reel.py jobs/<job>.json story --stills

Uses the job's "feature" cards (one photo each). Fonts, brandmark and type sizes come from carousel.py, so the
words sit exactly as they do on the carousel cards. Add music in Instagram.
"""
import argparse, json, os, subprocess, sys
import numpy as np
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import carousel as cz

FORMATS = {   # size, title baseline (TY), footage crop to that shape
    "post":  dict(W=1080, H=1350, TY=769,  crop="crop=864:1080:528:0,scale=1080:1350:flags=lanczos"),
    "story": dict(W=1080, H=1920, TY=1180, crop="crop=608:1080:656:0,scale=1080:1920:flags=lanczos"),  # words clear of the story UI
}
COVER, STEP, XF, END, ZOOM = 3.0, 2.4, 0.5, 1.0, 0.06

def shade(W, H, TY):
    y = np.linspace(0, 1, H)[:, None, None]; top = (TY - 0.27 * H) / H
    return 0.97 - 0.62 * np.clip((y - top) / 0.30, 0, 1)

class Reel:
    def __init__(self, job_path, fmt):
        self.job = json.load(open(job_path)); self.m = cz.Media(job_path, self.job)
        f = FORMATS[fmt]; self.W, self.H, self.TY, self.crop = f["W"], f["H"], f["TY"], f["crop"]
        self.S = shade(self.W, self.H, self.TY)
        self.cards = [c["feature"] for c in self.job["cards"] if "feature" in c]
        x_key = f"x_{fmt}"
        self.shots = [(c["shots"][0][0], c.get(x_key, c["shots"][0][1])) for c in self.cards]
        self._im = {}
        self.duration = COVER + len(self.cards) * STEP + END
        self._cover = None

    # ---- pictures
    def cover_frames(self):
        if self._cover is None:
            a, b = self.job["cover"]["footage"]; W, H = self.W, self.H
            slow = max(1.0, (COVER + XF) / (b - a))       # a short shot is slowed to cover the time
            raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-ss", f"{a:.3f}", "-t", f"{b - a:.3f}", "-i", self.m.footage, "-an",
                                  "-vf", f"setpts={slow}*PTS,{self.crop},fps={cz.FPS}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
            fr = np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)
            y = np.linspace(0, 1, H)[:, None, None]; top = (self.TY - 0.27 * H) / H
            sh = 0.85 - 0.30 * np.clip((y - top) / 0.30, 0, 1)
            self._cover = [Image.fromarray((f.astype(float) * sh).astype(np.uint8)) for f in fr]
        return self._cover
    def photo(self, i, p):
        """Card i's photo at push-in progress p (0..1)."""
        W, H = self.W, self.H
        if i not in self._im:
            src, x = self.shots[i]; im = Image.open(self.m.path(src)).convert("RGB")
            sc = (1 + ZOOM) * max(H / im.height, W / im.width)
            im = im.resize((round(im.width * sc), round(im.height * sc)), Image.LANCZOS)
            cx = W * (1 + ZOOM) / 2 + (im.width - W * (1 + ZOOM)) * float(x)
            self._im[i] = (im, cx, im.height / 2)
        im, cx, cy = self._im[i]; s = (1 + ZOOM * min(1, max(0, p))) / (1 + ZOOM); w, h = W / s, H / s
        w, h = min(w, im.width), min(h, im.height)
        x0 = min(max(0.0, cx - w / 2), im.width - w); y0 = min(max(0.0, cy - h / 2), im.height - h)
        a = np.asarray(im.resize((W, H), Image.BILINEAR, box=(x0, y0, x0 + w, y0 + h))).astype(float)
        return Image.fromarray((a * self.S).astype(np.uint8))

    # ---- words: same fonts, sizes and gaps as the carousel cards
    def words(self, c, title, caps, lines, alpha):
        if alpha <= 0: return
        l = Image.new("RGBA", (self.W, 400), (0, 0, 0, 0)); d = ImageDraw.Draw(l)
        d.text((0, 0), title, font=cz.HEAD, fill=cz.WHITE)
        cz.tracked(d, (0, cz.SUB_DY + cz.LABEL_DY), caps.upper(), cz.LABEL, cz.WHITE, 5.0)
        for k, ln in enumerate(lines):
            if ln: cz.tracked(d, (0, 195 + k * 40), ln.upper(), cz.LABEL, cz.WHITE, 5.0)
        if alpha < 1: l.putalpha(l.getchannel("A").point(lambda v: int(v * alpha)))
        c.paste(l, (64, self.TY), l)
    def text_for(self, i):
        if i < 0: cv = self.job["cover"]; return cv["title"], self.m.caps, []
        f = self.cards[i]; return f["title"], f["suburb"], f.get("lines", [])

    # ---- timeline
    def frame(self, t):
        n = len(self.cards); i = min(n - 1, int((t - COVER) // STEP)) if t >= COVER else -1
        start = COVER + i * STEP if i >= 0 else 0.0
        def pic(j, tt):
            if j < 0: fr = self.cover_frames(); return fr[min(int(tt * cz.FPS), len(fr) - 1)]
            return self.photo(j, (tt - (COVER + j * STEP)) / (STEP + XF + (END if j == n - 1 else 0)))
        a = (t - start) / XF if i >= 0 and t - start < XF else 1.0
        c = pic(i, t)
        if a < 1: c = Image.blend(pic(i - 1, t), c, a * a * (3 - 2 * a))
        c = c.copy(); c.paste(cz.ICON, (60, self.TY - 104), cz.ICON)
        if a < 1:
            self.words(c, *self.text_for(i - 1), max(0, 1 - 2 * a)); self.words(c, *self.text_for(i), max(0, 2 * a - 1))
        else: self.words(c, *self.text_for(i), 1)
        return c
    def render(self, out):
        W, H = self.W, self.H; tmp = os.path.join(os.path.dirname(out), ".tmp_" + os.path.basename(out))
        p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(cz.FPS),
                              "-i", "-", "-c:v", "libx264", "-crf", "18", "-preset", "veryfast", "-pix_fmt", "yuv420p", "-movflags", "+faststart", tmp],
                             stdin=subprocess.PIPE)
        for f in range(round(self.duration * cz.FPS)): p.stdin.write(self.frame(f / cz.FPS).tobytes())
        p.stdin.close(); assert p.wait() == 0; os.replace(tmp, out)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("job"); ap.add_argument("fmt", choices=FORMATS); ap.add_argument("--stills", action="store_true")
    a = ap.parse_args(); r = Reel(a.job, a.fmt)
    name = os.path.splitext(os.path.basename(a.job))[0]; out_dir = os.path.join(HERE, "out", name); os.makedirs(out_dir, exist_ok=True)
    if a.stills:
        ts = [2.0] + [COVER + i * STEP + XF + 0.2 for i in range(len(r.cards))]
        tw, th = 270, round(270 * r.H / r.W); cols = 7
        s = Image.new("RGB", (cols * (tw + 4), ((len(ts) + cols - 1) // cols) * (th + 4)), "white")
        for k, t in enumerate(ts): s.paste(r.frame(t).resize((tw, th)), ((k % cols) * (tw + 4), (k // cols) * (th + 4)))
        out = os.path.join(out_dir, f"reel_{a.fmt}_stills.jpg"); s.save(out, quality=88); print(out); return
    out = os.path.join(out_dir, f"{r.job['name']} ({a.fmt}).mp4"); r.render(out); print(out, round(r.duration, 1), "s")

if __name__ == "__main__":
    main()
