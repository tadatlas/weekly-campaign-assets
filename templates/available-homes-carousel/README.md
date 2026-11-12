# Available Homes carousel (Instagram, video cards)

An Instagram carousel that gives every home for sale in a region some exposure. It was first made for the Lower North Shore on 12 November 2026. `jobs/lns-12nov2026.json` is that carousel, and rendering it reproduces the posted files frame for frame.

## Make one

1. **Footage.** Download the region's lifestyle clips from the Atlas iQ Lifestyle Gallery (category "<Region> Lifestyle Clips (Collated)") into `jobs/footage/`. The folder is gitignored, so footage is never committed.
2. **Job file.** Copy `jobs/lns-12nov2026.json` and fill it in. See **Job file** below.
3. **Stills first:**
   ```
   python3 carousel.py jobs/<job>.json --stills
   ```
   This writes `out/<job>/stills.jpg` with the cover, every suburb intro and the first frame of every list. Get it approved before rendering.
4. **Render:**
   ```
   python3 carousel.py jobs/<job>.json            # all cards
   python3 carousel.py jobs/<job>.json --cards 2  # one card (1 = cover)
   ```
   The files go to `out/<job>/`. Fonts download on the first run (`fonts.py`). Needs Python 3, Pillow, numpy, fontTools and ffmpeg.
5. **Post.** Add the cards in number order, add music in Instagram, and put "for sale" in the caption. The cards themselves never say it.

## Locked design

- **Cards:** 1080 × 1350 video, 30 fps. The photo panel is the top 600 px, with a Stone panel below.
- **Fixed positions:** the brandmark (78 px), the Rhymes Light 84 title and the Fakt caps line sit in exactly the same place on every card and every frame. That's what makes the match cuts work. Never move them for one card.
- **Cover:** lifestyle footage, darkened. It shows the region name in Rhymes with AVAILABLE HOMES under it.
- **Suburb cards:** one card per suburb group.
  - The card opens on a footage shot per suburb, with the suburb name and AVAILABLE HOMES. Each shot is a hard cut: 0.6 s per suburb, or 1.2 s when there's only one. The last suburb shown is the first home's suburb.
  - It then cuts straight to the list. The title line becomes the address, and the caps line becomes that home's suburb.
- **The list:**
  - Five homes per column, 10 per page, sorted A to Z by street name without the number. The list has no suburb labels, because the suburb sits under the address.
  - Every second the photo, address and suburb move to the next home. The active home is white and the others are dimmed.
  - When a page is done, the whole list scrolls up, as in the OFI story template, and the next page comes in from below.
  - After the last home, every row turns white and holds for 2 s.

## Content rules

- **Features:** use "5 BEDS   4 BATHS   4 CARS", with plurals handled and zeros left out. Land size goes in only when there's nothing else (e.g. "763 SQM"). The script stops if a 0 gets through.
- **One entry per listing:** the website sometimes lists a property twice (e.g. a relisted unit). Include it once. The script stops on a duplicate street.
- **Check stock on the day:** check every home is still for sale on the day you post, using the daily website property sync. A new listing must go in.
- **Photo crops:** check every photo in its 1080 × 600 crop. Swap photos with baked-in graphics (map pins, site boundaries) for the next gallery photo.
- **Renders:** set `"render": true` on any home whose photo is a render. That adds the Artist Impression label, which the crop would otherwise cut off.
- **Suburb footage:** a recognisable place only appears under its own suburb (Balmoral footage only for Mosman). Suburbs without footage get neutral shots: people, coffee, water, sunsets.
- **Small groups:** where a group only has a couple of homes from outside the region's core, give it one combined title on two lines (`title_lines`) instead of one name per suburb, e.g. "Northern Beaches &" / "Upper North Shore".

## Job file

```json
{
  "name": "LNS Available Homes Carousel",          // also the output file name
  "footage": "footage/lns_clips.mp4",               // relative to the job file
  "cover": {"title": "Lower North Shore", "footage": [33.6, 39.5]},
  "cards": [
    {"name": "Mosman",
     "intro": {"titles": ["Mosman"], "shots": [[29.53, 32.03, 1]]},   // [start, end, slow-down]
     "homes": [{"street": "201/171-179 Avenue Road", "suburb": "Mosman",
                "features": "2 BEDS   2 BATHS   2 CARS", "photo": "<image url>", "render": false}]}
  ]
}
```

- `shots` are seconds in the footage. Use one shot per suburb and keep each shot to a single take with no cut inside it. A slow-down above 1 stretches a short shot so it covers the time.
- `titles` must end on the first home's suburb. The script checks this.
- `title_lines` replaces `titles` for a combined group title.

## Files

| File | What it is |
| --- | --- |
| `carousel.py` | The renderer: the cover, the suburb cards, stills mode and the content checks |
| `fonts.py` | Fetches Rhymes and Fakt from `tadatlas/atlas-app-fonts` and converts them to TTF |
| `assets/` | The white brandmark and the Artist Impression label |
| `jobs/lns-12nov2026.json` | The first carousel: Lower North Shore, 39 homes, 6 cards |
