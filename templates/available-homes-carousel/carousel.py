"""Available Homes Instagram carousel (1080x1350 video cards).

    python3 carousel.py jobs/<job>.json                 # render every card into out/<job>/
    python3 carousel.py jobs/<job>.json --cards 1 3     # render some cards (1 = cover)
    python3 carousel.py jobs/<job>.json --stills        # contact sheet of key frames, no video

Card 1 is the cover: lifestyle footage, the region in Rhymes, AVAILABLE HOMES under it.
Every other card is one suburb group:
  1. Intro: a footage shot per suburb with its name, hard cuts (0.6s each, 1.2s if one suburb).
     The last suburb shown is the first home's suburb.
  2. Match cut into the list: the brandmark, title line and caps line never move between the
     cover, the intros and the list. Only the words and the picture change.
  3. The list: 5 homes per column, 10 per page. The photo, address and suburb step to the next
     home every second; the active home is white, the rest dim. When a page is done, the whole
     list scrolls up (like the OFI story template) and the next page comes in from below.
"""
import re, argparse, hashlib, json, os, subprocess, sys, urllib.request
import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import fonts as _fonts

# ------------------------------------------------------------------ locked design
W, H, FPS = 1080, 1350, 30
STONE, WHITE, GREY, DIM = (30, 30, 30), (255, 255, 255), (160, 160, 158), (150, 150, 148)
PHOTO_H = Y0 = 600
COLX = (64, 556)
HEAD_Y, SUB_DY = Y0 + 169, 98          # Rhymes 84 title, Fakt caps line under it
ICON_XY = (60, Y0 + 65)                # brandmark (78px)
LIST_Y, ROW_H, PER_COL = Y0 + 326, 66, 5
PAGE_STEP = PER_COL * ROW_H + 60
TOP_CLIP, BOT_CLIP = LIST_Y - 14, 1300
STEP, XF, HOLD, ZOOM, SCROLL_T = 1.0, 0.3, 2.0, 0.05, 1.3
PER_SINGLE, PER_MULTI, LINE = 1.8, 1.2, 92
XS = 0.4                               # dissolve between suburb shots
FADE = 0.5                             # intro dissolves into the list; words swap out then in
CROP = "crop=864:1080:528:0,scale=1080:1350:flags=lanczos"     # 16:9 footage to 4:5

F = _fonts.ensure()
HEAD = ImageFont.truetype(f"{F}/RhymesDisplay-Light.ttf", 84)
FAKT_MED = ImageFont.truetype(f"{F}/Fakt-Medium.ttf", 28)
LABEL = ImageFont.truetype(f"{F}/Fakt-SemiBold.ttf", 20)          # caps line: Fakt SemiBold, 0.25em tracking
LABEL_DY = FAKT_MED.getbbox("H")[1] - LABEL.getbbox("H")[1]          # keep the caps' top where it was
FAKT_XS = ImageFont.truetype(f"{F}/Fakt-Medium.ttf", 17)
FAKT = ImageFont.truetype(f"{F}/Fakt-Normal.ttf", 29)
ICON = Image.open(f"{HERE}/assets/brandmark_white.png").convert("RGBA").resize((78, 78), Image.LANCZOS)
_lab = Image.open(f"{HERE}/assets/artist_impression_label.png").convert("RGBA")
AI_LABEL = _lab.resize((_lab.width // 2, _lab.height // 2), Image.LANCZOS)
SCRIM = Image.new("RGBA", (W, 150), (0, 0, 0, 0))
SCRIM.putalpha(Image.linear_gradient("L").resize((W, 150)).point(lambda v: int(v * 0.45)))
_y = np.linspace(0, 1, H)[:, None, None]
SHADE_INTRO = np.where(_y > 0.45, 0.62 - 0.12 * (_y - 0.45) / 0.55, 0.62 - 0.22 * np.clip((0.45 - _y) / 0.45, 0, 1))
SHADE_COVER = np.where(_y > 0.45, 0.72 - 0.10 * (_y - 0.45) / 0.55, 0.72 + 0.13 * np.clip((0.45 - _y) / 0.45, 0, 1))
MASK = Image.new("L", (W, H), 0)
_d = ImageDraw.Draw(MASK)
_d.rectangle((0, TOP_CLIP + 20, W, BOT_CLIP - 30), fill=255)
for k in range(20): _d.line((0, TOP_CLIP + k, W, TOP_CLIP + k), fill=int(255 * k / 20))
for k in range(30): _d.line((0, BOT_CLIP - 30 + k, W, BOT_CLIP - 30 + k), fill=int(255 * (1 - k / 30)))

def tracked(d, xy, txt, font, fill, tr=0.0):
    x, y = xy
    for ch in txt:
        d.text((x, y), ch, font=font, fill=fill); x += font.getlength(ch) + tr

def title_block(c, lines, caps, alpha=1.0, caps_alpha=None):
    """Rhymes line(s) at HEAD_Y with a Fakt caps line under the last one.
    caps_alpha lets the caps line hold steady while the title fades (suburb to suburb)."""
    caps_alpha = alpha if caps_alpha is None else caps_alpha
    for part, a in (("title", alpha), ("caps", caps_alpha)):
        if a <= 0: continue
        l = Image.new("RGBA", (W - 64, 140 + LINE * (len(lines) - 1)), (0, 0, 0, 0)); d = ImageDraw.Draw(l)
        if part == "title":
            for k, ln in enumerate(lines):
                assert HEAD.getlength(ln) <= W - 128, f"too long for one line: {ln}"
                d.text((0, k * LINE), ln, font=HEAD, fill=WHITE)
        else: tracked(d, (0, SUB_DY + LABEL_DY + LINE * (len(lines) - 1)), caps.upper(), LABEL, WHITE, 5.0)
        if a < 1: l.putalpha(l.getchannel("A").point(lambda v: int(v * a)))
        c.paste(l, (64, HEAD_Y), l)

# ------------------------------------------------------------------ media
def shifted(crop, dx):
    """The footage crop moved dx source pixels sideways (negative = left), kept inside the 1920px frame."""
    if not dx: return crop
    w, h, x, y = map(int, re.match(r"crop=(\d+):(\d+):(\d+):(\d+)", crop).groups())
    return crop.replace(f"crop={w}:{h}:{x}:{y}", f"crop={w}:{h}:{max(0, min(1920 - w, x + dx))}:{y}", 1)

class Media:
    def __init__(self, job_path, job):
        self.root = os.path.dirname(os.path.abspath(job_path))
        self.cache = os.path.join(HERE, "out", ".cache"); os.makedirs(self.cache, exist_ok=True)
        self.footage = self.path(job.get("footage")) if job.get("footage") else None
        self._ph, self._shots = {}, {}
        self.caps = job.get("caps", "Available homes")      # caps line on the cover and intros
    def path(self, p):
        if p.startswith("http"):
            dst = os.path.join(self.cache, hashlib.md5(p.encode()).hexdigest() + ".jpg")
            if not os.path.exists(dst):
                req = urllib.request.Request(p, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req) as r, open(dst, "wb") as f: f.write(r.read())
            return dst
        return p if os.path.isabs(p) else os.path.join(self.root, p) if os.path.exists(os.path.join(self.root, p)) else os.path.join(HERE, p)
    def panel(self, home, z, t, window):
        """The top panel for a home t seconds into its window on screen: its "clip" (a short video, one shot,
        no titles) when it has one, slowed to fill the window if it is too short; otherwise its photo with push-in."""
        if home.get("photo2") and not home.get("clip"):     # two photos: dissolve to the second halfway through
            sw = (window - XF) / 2; second = dict(home, photo=home["photo2"])
            z1 = ZOOM * max(0, min(1, t / (sw + XF))); z2 = ZOOM * max(0, min(1, (t - sw) / (window - sw)))
            if t < sw: return self.photo(home, z1)
            if t >= sw + XF: return self.photo(second, z2)
            a = (t - sw) / XF; return Image.blend(self.photo(home, z1), self.photo(second, z2), a * a * (3 - 2 * a))
        if not home.get("clip"): return self.photo(home, z)
        key = home["clip"]
        if key not in self._ph:
            raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-i", self.path(key), "-an", "-vf",
                                  f"scale={W}:{PHOTO_H}:force_original_aspect_ratio=increase:flags=lanczos,crop={W}:{PHOTO_H},fps={FPS}",
                                  "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True, check=True).stdout
            self._ph[key] = [Image.fromarray(f) for f in np.frombuffer(raw, np.uint8).reshape(-1, PHOTO_H, W, 3)]
        fr = self._ph[key]; slow = max(1.0, window * FPS / len(fr))
        out = fr[min(len(fr) - 1, max(0, int(t * FPS / slow)))]
        if home.get("render"):
            out = out.copy(); out.paste(SCRIM, (0, PHOTO_H - SCRIM.height), SCRIM)
            out.paste(AI_LABEL, (W - 64 - AI_LABEL.width, PHOTO_H - AI_LABEL.height - 22), AI_LABEL)
        return out
    def photo(self, home, z):
        """Home photo for the top panel, slow zoom z (0..ZOOM). Renders keep an Artist Impression label."""
        key = home["photo"]
        if key not in self._ph:
            im = Image.open(self.path(key)).convert("RGB")
            sc = max(W * (1 + ZOOM) / im.width, PHOTO_H * (1 + ZOOM) / im.height)
            self._ph[key] = im.resize((round(im.width * sc), round(im.height * sc)), Image.LANCZOS)
        im = self._ph[key]; s = (1 + z) / (1 + ZOOM)
        w, h = W / s, PHOTO_H / s; x, y = (im.width - w) / 2, (im.height - h) / 2
        out = im.resize((W, PHOTO_H), Image.BILINEAR, box=(x, y, x + w, y + h))
        if home.get("render"):
            out.paste(SCRIM, (0, PHOTO_H - SCRIM.height), SCRIM)
            out.paste(AI_LABEL, (W - 64 - AI_LABEL.width, PHOTO_H - AI_LABEL.height - 22), AI_LABEL)
        return out
    def clip(self, a, b, slow=1.0, shade=SHADE_INTRO, trim=0.05, dur=None, shift=0):
        """Frames of footage a..b seconds, portrait crop, darkened. slow>1 plays it slower.
        A still instead of footage: a = image path, b = horizontal crop position (0 left .. 1 right),
        played for dur seconds with the same slow push-in as the home photos."""
        key = (a, b, slow, id(shade), dur, shift)
        if key not in self._shots:
            if isinstance(a, str):
                im = Image.open(self.path(a)).convert("RGB"); sc = (1 + ZOOM) * max(H / im.height, W / im.width)
                im = im.resize((max(round(im.width * sc), round(W * (1 + ZOOM))), max(round(im.height * sc), round(H * (1 + ZOOM)))), Image.LANCZOS)
                cx = W * (1 + ZOOM) / 2 + (im.width - W * (1 + ZOOM)) * float(b); cy = im.height / 2
                n = max(1, round((dur or 1.0) * FPS)); fr = []
                for i in range(n):
                    s = (1 + ZOOM * i / max(1, n - 1)) / (1 + ZOOM); w, h = W / s, H / s
                    fr.append(np.asarray(im.resize((W, H), Image.BILINEAR, box=(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2))))
            else:
                raw = subprocess.run(["ffmpeg", "-loglevel", "error", "-ss", f"{a + trim:.3f}", "-t", f"{b - a - 2 * trim:.3f}", "-i", self.footage,
                                      "-an", "-vf", f"setpts={slow}*PTS,{shifted(CROP, shift)},fps={FPS}", "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
                                     capture_output=True, check=True).stdout
                fr = np.frombuffer(raw, np.uint8).reshape(-1, H, W, 3)
            self._shots[key] = [Image.fromarray((f.astype(float) * shade).astype(np.uint8)) for f in fr]
        return self._shots[key]

# ------------------------------------------------------------------ cover
def cover_frames(job, m):
    cv = job["cover"]
    if "image" in cv: fr = m.clip(cv["image"], cv.get("x", 0.5), 1.0, SHADE_COVER, dur=cv.get("duration", 5.0))
    else:                                    # [start, end] or [start, end, slow-down]
        a, b, *slow = cv["footage"]; fr = m.clip(a, b, slow[0] if slow else 1.0, SHADE_COVER, trim=0.0, shift=cv.get("shift", 0))
    for f in fr:
        c = f.copy(); c.paste(ICON, ICON_XY, ICON)
        title_block(c, job["cover"].get("title_lines", [job["cover"]["title"]]), m.caps)
        yield c

# ------------------------------------------------------------------ suburb card
class Card:
    def __init__(self, card, m):
        self.c, self.m, self.homes = card, m, card["homes"]
        self.rows = []
        for i, h in enumerate(self.homes):
            page, r = divmod(i, PER_COL * 2); ci, j = divmod(r, PER_COL)
            self.rows.append((ci, LIST_Y + page * PAGE_STEP + j * ROW_H))
        intro = card.get("intro") or {"shots": []}; self.shots = intro["shots"]
        self.lines = intro.get("title_lines")
        self.titles = intro.get("titles")
        if self.titles:
            assert len(self.titles) == len(self.shots), card["name"]
            assert self.titles[-1] == self.homes[0]["suburb"], f"{card['name']}: intro must end on the first home's suburb"
        self.per = PER_SINGLE if len(self.shots) == 1 else PER_MULTI
        self.intro_len = self.per * len(self.shots)
        self.fade = FADE if self.shots else 0.0          # no intro: the card opens on the list
        n = len(self.homes)
        self.list_len = self.start(n - 1) + STEP + HOLD
        self.duration = self.intro_len + self.fade + self.list_len
    def page(self, i): return i // (PER_COL * 2)
    def start(self, i): return i * STEP + self.page(i) * SCROLL_T
    def scroll(self, t):
        n, v = len(self.homes), 0.0
        for p in range(1, self.page(n - 1) + 1):
            ts = self.start(p * PER_COL * 2) - SCROLL_T
            if t >= ts:
                x = min(1.0, (t - ts) / SCROLL_T); v = (p - 1 + x * x * (3 - 2 * x)) * PAGE_STEP
        return v
    def shot(self, i):
        """Shot i's frames, long enough to cover its time on screen plus the dissolve out of it."""
        a, b, slow = (self.shots[i] + [1.0])[:3]; need = self.per + XS
        if isinstance(a, str): return self.m.clip(a, b, slow, dur=need)
        return self.m.clip(a, b, max(slow, need / (b - a - 0.1)))
    def intro_frame(self, t, title=True):
        i = min(int(t // self.per), len(self.shots) - 1); tl = t - i * self.per
        at = lambda fr, x: fr[min(int(x * FPS), len(fr) - 1)]
        c = at(self.shot(i), tl)
        a = tl / XS if (i > 0 and tl < XS) else 1.0
        if a < 1: c = Image.blend(at(self.shot(i - 1), self.per + tl), c, a * a * (3 - 2 * a))
        c = c.copy(); c.paste(ICON, ICON_XY, ICON)
        if title:
            if self.lines: title_block(c, self.lines, self.m.caps)
            elif a < 0.5: title_block(c, [self.titles[i - 1]], self.m.caps, 1 - 2 * a, caps_alpha=1)
            else: title_block(c, [self.titles[i]], self.m.caps, min(1, 2 * a - 1) if a < 1 else 1, caps_alpha=1)
        return c
    def list_frame(self, t, title=True):
        n = len(self.homes)
        k = max([i for i in range(n) if self.start(i) <= t] or [0]); ts = self.start(k)
        def pic(i):
            e = (self.start(i + 1) + XF if i < n - 1 else self.list_len) - self.start(i)
            z = ZOOM * max(0, min(1, (t - self.start(i)) / e))
            return self.m.panel(self.homes[i], z, t - self.start(i), e)
        cur = pic(k)
        a = min(1, max(0, (t - ts) / XF)) if k > 0 else 1
        if a < 1: cur = Image.blend(pic(k - 1), cur, a)
        c = Image.new("RGB", (W, H), STONE); c.paste(cur, (0, 0)); c.paste(ICON, ICON_XY, ICON)
        if title:
            if a < 1: title_block(c, [self.homes[k - 1]["street"]], self.homes[k - 1]["suburb"], max(0, 1 - 2 * a))
            title_block(c, [self.homes[k]["street"]], self.homes[k]["suburb"], max(0, 2 * a - 1) if a < 1 else 1)
        sc, done = self.scroll(t), t >= self.start(n - 1) + STEP
        lc = Image.new("RGBA", (W, H), (0, 0, 0, 0)); ld = ImageDraw.Draw(lc)
        for i, (ci, y) in enumerate(self.rows):
            yy = y - sc
            if yy > H or yy + 70 < 0: continue
            h = self.homes[i]
            ld.text((COLX[ci], yy), h["street"], font=FAKT, fill=WHITE if (i == k or done) else DIM)
            if h.get("features"): tracked(ld, (COLX[ci], yy + 35), h["features"], FAKT_XS, GREY, 2.4)
        lc.putalpha(ImageChops.multiply(lc.getchannel("A"), MASK)); c.paste(lc, (0, 0), lc)
        return c
    def fade_frame(self, t):
        a = t / FADE; e = a * a * (3 - 2 * a)
        c = Image.blend(self.intro_frame(self.intro_len - 1 / FPS, title=False), self.list_frame(0, title=False), e)
        c.paste(ICON, ICON_XY, ICON)
        if a < 0.5: title_block(c, self.lines if self.lines else [self.titles[-1]], self.m.caps, 1 - 2 * a)
        else: title_block(c, [self.homes[0]["street"]], self.homes[0]["suburb"], 2 * a - 1)
        return c
    def frame(self, t):
        if t < self.intro_len: return self.intro_frame(t)
        if t < self.intro_len + self.fade: return self.fade_frame(t - self.intro_len)
        return self.list_frame(t - self.intro_len - self.fade)
    def frames(self):
        for f in range(round(self.duration * FPS)): yield self.frame(f / FPS)

# ------------------------------------------------------------------ feature card
_yf = np.linspace(0, 1, H)[:, None, None]
SHADE_FEATURE = 0.97 - 0.62 * np.clip((_yf - 0.28) / 0.40, 0, 1)   # photo stays bright up top, dark under the words
INFO_Y, INFO_STEP = LIST_Y + 38, 40              # one clear space under the suburb, matching the spacer lines

class Feature:
    """One home, full bleed: its photos dissolve into each other under a fixed title (address, suburb)
    with info lines below (features, rent or price, inspection)."""
    def __init__(self, card, m):
        f = card["feature"]; self.m, self.f = m, f
        self.shots, self.per = f["shots"], f.get("per", 1.8)
        self.duration = self.per * len(self.shots) + XS
    def shot(self, i):
        a, b = self.shots[i][:2]; return self.m.clip(a, b, 1.0, SHADE_FEATURE, dur=self.per + XS)
    def frame(self, t):
        i = min(int(t // self.per), len(self.shots) - 1); tl = t - i * self.per
        at = lambda fr, x: fr[min(int(x * FPS), len(fr) - 1)]
        c = at(self.shot(i), tl)
        a = tl / XS if (i > 0 and tl < XS) else 1.0
        if a < 1: c = Image.blend(at(self.shot(i - 1), self.per + tl), c, a * a * (3 - 2 * a))
        c = c.copy(); c.paste(ICON, ICON_XY, ICON)
        title_block(c, [self.f["title"]], self.f["suburb"])
        d = ImageDraw.Draw(c)
        for k, ln in enumerate(self.f.get("lines", [])):      # "" leaves a line's space
            if ln: tracked(d, (64, INFO_Y + k * INFO_STEP), ln.upper(), LABEL, WHITE, 5.0)
        return c
    def frames(self):
        for f in range(round(self.duration * FPS)): yield self.frame(f / FPS)
    def stills(self): return [self.frame(i * self.per + self.per / 2) for i in range(len(self.shots))]

# ------------------------------------------------------------------ output
def encode(frames, out):
    tmp = os.path.join(os.path.dirname(out), ".tmp_" + os.path.basename(out))
    p = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS),
                          "-i", "-", "-c:v", "libx264", "-crf", "18", "-preset", "veryfast", "-pix_fmt", "yuv420p",
                          "-movflags", "+faststart", tmp], stdin=subprocess.PIPE)
    for f in frames: p.stdin.write(f.tobytes())
    p.stdin.close(); assert p.wait() == 0, out
    os.replace(tmp, out)

def check(job):
    """Content rules: never a 0 in features, no listing twice, intro ends on the first home's suburb."""
    seen = set()
    for c in job["cards"]:
        for h in c.get("homes", []):
            k = (h["street"], h["suburb"]); assert k not in seen, f"duplicate listing: {h['street']}"; seen.add(k)
            assert not any(w == "0" for w in h.get("features", "").split()), f"zero in features: {h['street']}"

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("job"); ap.add_argument("--cards", type=int, nargs="*"); ap.add_argument("--stills", action="store_true")
    a = ap.parse_args()
    job = json.load(open(a.job)); check(job); m = Media(a.job, job)
    name = os.path.splitext(os.path.basename(a.job))[0]
    out_dir = os.path.join(HERE, "out", name); os.makedirs(out_dir, exist_ok=True)
    cards = [Feature(c, m) if "feature" in c else Card(c, m) for c in job["cards"]]
    if a.stills:
        shots = [next(iter(cover_frames(job, m)))]
        for c in cards:
            if isinstance(c, Feature): shots += c.stills(); continue
            shots += [c.intro_frame(i * c.per + c.per / 2) for i in range(len(c.shots))] + [c.list_frame(0.2)]
        cols = 6; s = Image.new("RGB", (cols * 275, ((len(shots) + cols - 1) // cols) * 343), "white")
        for i, im in enumerate(shots): s.paste(im.resize((270, 338)), ((i % cols) * 275, (i // cols) * 343))
        s.save(os.path.join(out_dir, "stills.jpg"), quality=88); print(os.path.join(out_dir, "stills.jpg")); return
    want = a.cards or list(range(1, len(cards) + 2))
    for n in want:
        out = os.path.join(out_dir, f"{job['name']} {n:02d}.mp4")
        if n == 1: encode(cover_frames(job, m), out); print(out)
        elif job["cards"][n - 2].get("still"):          # a still card: one image, no motion
            out = out[:-4] + ".jpg"; cards[n - 2].frame(0).save(out, quality=95); print(out)
        else: encode(cards[n - 2].frames(), out); print(out, round(cards[n - 2].duration, 1), "s")

if __name__ == "__main__":
    main()
