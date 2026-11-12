"""Story version (1080 x 1920) of an Available Homes carousel job: the same cards, words and timing on the open home
story grid (photo panel 1040px tall, Stone panel below; lists stop above the Instagram reply bar).

    python3 story.py jobs/<job>.json --stills
    python3 story.py jobs/<job>.json            # one MP4 per frame: cover, then one per suburb card

Optional per-home "photo_story" (and "x_story") picks a different photo or crop for the taller story panel.
Optional per-home "clip_story" plays a short video in the panel instead of the photo: one clean shot (no title
cards, badges or people), cut from the home's property video. 1-3 seconds is enough; a short clip is slowed to fill.
"""
import argparse, json, os, sys
import numpy as np
from PIL import Image, ImageDraw
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import carousel as cz

# ---- the carousel grid, moved down to the story photo height (matches the open home stories within 3px)
cz.H, cz.PHOTO_H = 1920, 1040
cz.Y0 = cz.PHOTO_H
cz.ICON_XY = (60, cz.Y0 + 65)
cz.HEAD_Y = cz.Y0 + 169
cz.LIST_Y = cz.Y0 + 326
cz.TOP_CLIP, cz.BOT_CLIP = cz.LIST_Y - 14, 1720                   # nothing under the reply bar
cz.CROP = "crop=608:1080:656:0,scale=1080:1920:flags=lanczos"      # 16:9 footage to 9:16
_y = np.linspace(0, 1, cz.H)[:, None, None]; top = cz.Y0 / cz.H - 0.07
cz.SHADE_INTRO = np.where(_y > top, 0.62 - 0.12 * (_y - top) / (1 - top), 0.62 - 0.22 * np.clip((top - _y) / top, 0, 1))
cz.SHADE_COVER = np.where(_y > top, 0.72 - 0.10 * (_y - top) / (1 - top), 0.72 + 0.13 * np.clip((top - _y) / top, 0, 1))
cz.Media.clip.__defaults__ = (1.0, cz.SHADE_INTRO, 0.05, None)    # its default shade was bound at import
cz.MASK = Image.new("L", (cz.W, cz.H), 0); _d = ImageDraw.Draw(cz.MASK)
_d.rectangle((0, cz.TOP_CLIP + 20, cz.W, cz.BOT_CLIP - 30), fill=255)
for k in range(20): _d.line((0, cz.TOP_CLIP + k, cz.W, cz.TOP_CLIP + k), fill=int(255 * k / 20))
for k in range(30): _d.line((0, cz.BOT_CLIP - 30 + k, cz.W, cz.BOT_CLIP - 30 + k), fill=int(255 * (1 - k / 30)))

def story_job(job):
    for c in job["cards"]:
        for h in c.get("homes", []):
            if "photo_story" in h: h["photo"] = h["photo_story"]
            if "clip_story" in h: h["clip"] = h["clip_story"]
    return job

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("job"); ap.add_argument("--stills", action="store_true"); ap.add_argument("--cards", type=int, nargs="*")
    a = ap.parse_args()
    job = story_job(json.load(open(a.job))); cz.check(job); m = cz.Media(a.job, job)
    name = os.path.splitext(os.path.basename(a.job))[0] + "-story"
    out_dir = os.path.join(HERE, "out", name); os.makedirs(out_dir, exist_ok=True)
    cards = [cz.Card(c, m) for c in job["cards"]]
    if a.stills:
        shots = [next(iter(cz.cover_frames(job, m)))]
        for c in cards: shots += [c.intro_frame(c.per / 2), c.list_frame(0.2), c.list_frame(c.list_len - 0.3)]
        tw, th, cols = 270, 480, 7
        s = Image.new("RGB", (cols * (tw + 4), ((len(shots) + cols - 1) // cols) * (th + 4)), "white")
        for i, im in enumerate(shots): s.paste(im.resize((tw, th)), ((i % cols) * (tw + 4), (i // cols) * (th + 4)))
        out = os.path.join(out_dir, "stills.jpg"); s.save(out, quality=88); print(out); return
    for n in (a.cards or range(1, len(cards) + 2)):
        out = os.path.join(out_dir, f"{job['name'].replace('Carousel', 'Story')} {n:02d}.mp4")
        if n == 1: cz.encode(cz.cover_frames(job, m), out); print(out)
        else: cz.encode(cards[n - 2].frames(), out); print(out, round(cards[n - 2].duration, 1), "s")
        m._ph.clear(); m._shots.clear()        # decoded clips are large: free them between frames

if __name__ == "__main__":
    main()
