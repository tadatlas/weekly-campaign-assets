# Open home Instagram stories (split card, full-bleed, cover)

The open home stories for sales and rentals (property management): three formats, the OPEN tag, the animation and the checks to run before a story goes out. The static cards are built in Canva from the reference designs below. `story_tools.py` renders the tag and animates the photos.

## Files

| File | What it is |
| --- | --- |
| `story_tools.py` | Renders the OPEN tag and animates a split card or full-bleed story (photos, crossfades, slow zoom). Needs Python 3, Pillow and ffmpeg |
| `reference/split-card.png` | Split card: Canva "SH – Story – Template" (`DAHZt9DJzXQ`), as at 25 Nov 2026. The tag is added in code |
| `reference/full-bleed.png` | Full-bleed: Canva "OFI Story Template Options", Option B (`DAHbavwou80`, page 2). Draft positions, before the 80px move. The small review label at the bottom is in the Canva draft, not part of the design |
| `reference/cover.png` | Cover: Canva "OFI Stories – Sat 21 Nov 2026 – v2 Option A – DRAFT" (`DAHba4SkpF0`, page 1) |
| `assets/brandmark_mask.png` | The Atlas brandmark, for code renders |
| `fonts.py` | Fetches Rhymes and Fakt for code renders into `fonts/` (gitignored) |

**Never commit font files.** This repo is public and Fakt and Rhymes are licensed. `story_tools.py` downloads Fakt Medium from atlas.com.au each run.

```
python3 story_tools.py tag "OPEN TODAY" "3:00 – 3:15PM" tag.png
python3 story_tools.py animate split card.png out.mp4 --tag=tag.png [--anchor=topleft] p1.jpg p2.jpg p3.jpg
python3 story_tools.py animate full overlay.png out.mp4 --tag=tag.png [--tagpos=64,1556] p1.jpg p2.jpg p3.jpg
```

## Open decisions

To be decided by Theo once, then recorded here.

1. **Full-bleed:** move the lower block up 80px so it clears the reply bar (recommended). *Pending.*
2. **Rental cover line wording**, e.g. `LOWER NORTH SHORE · FOR LEASE · TUESDAY 24 NOVEMBER`. *Pending. Ask before making a rental cover.*
3. **Tag on split cards:** every split card carries the baked-in tag (recommended), or the tag is left to the Instagram sticker. *Pending.*

## Formats

Canvas 1080 × 1920, margins 64px.

Colours (`atlasiqmarketing/brand/tokens.json`): Stone `#1E1E1E`, Sand `#EBE4DF`, Terra `#734137`, Ocean `#273B47`, White. Body text on white is `#1A1A1A`.

Fonts: Rhymes Text Light (headings), Fakt Pro Medium and Normal (labels and body). The webfont files are linked from `https://www.atlas.com.au/assets/main-*.css`. "Tracking 0.15" means Canva letter spacing 150.

### Split card (default: Lower North Shore sales and PM rentals)

Same geometry as Canva "PM – Story – Template" and "SH – Story – Template".

| Element | Spec |
|---|---|
| Media | x0 y0, 1080 × 1040, cover crop. Photo or MP4. Animated: 3 photos (see **Animation**) |
| Atlas icon (dark) | x64 y1107, 70 × 70 |
| Street | Rhymes Text Light 64px, `#1A1A1A`, line height 1.2, top 1211, width 952, one line, e.g. `6/3 Millett Road` |
| Suburb | Fakt Medium 28px caps, tracking 0.15, top 1292, e.g. `MOSMAN` |
| Features | Same style, top 1362. `2 BEDS       1 BATH       1 CAR       633 SQM`: 7 spaces between items, singular for 1, drop zeros, drop SQM if there's no land size, no comma in SQM |
| Body | Fakt Normal 33px, line height 1.5, top 1429, width 927. First sentence of the website description, word for word, max 3 lines |
| OPEN tag | x64 y852 (bottom left of the photo). See **OPEN tag** |

The SH 7 Nov cards in `stories/sh-07nov2026/` are an earlier layout: the street sits about 21px higher (cap top y1198 against y1219 on the current template). Use the current template.

### Full-bleed (vertical video or one standout photo only)

From Canva "OFI Story Template Options", Option B.

| Element | Spec |
|---|---|
| Media | Full frame, 1080 × 1920. A 3:2 landscape photo keeps only about 37% of its width at 9:16, so don't use full-bleed for standard listing photos |
| Overlays | Stone gradients for legibility: top ~45% at y0 fading to 0% at y440; bottom 0% at y1060 rising to ~50% at y1920. The Canva draft stacks Stone rectangles at 3.6–3.8% opacity; in code use linear gradients |
| Atlas icon (white) | x64 y246, 56 × 56 |
| Eyebrow | x140 y258, Fakt Medium 26px white caps, tracking 0.15: `OPEN HOMES · SATURDAY 21 NOVEMBER` |
| Suburb | x64, Fakt Medium 28px white caps, tracking 0.15 |
| Street | x64, Rhymes Text Light 76px white, line height 1.2, one line |
| OPEN tag | See **OPEN tag** |
| Vertical positions | The draft has suburb y1440, street y1484, tag y1636 (to 1760), which runs into Instagram's reply bar. Proposed: move all three up 80px (suburb 1360, street 1404, tag 1556) so everything stays above y1680. See **Open decisions** |

The draft's tag text is untracked Fakt Normal 28. Don't copy it; use the shared tag style.

### Cover (open homes list; one per region and day, overflow to "2 of 2")

From Canva "OFI Stories – Sat 21 Nov 2026 – v2 Option A – DRAFT", pages 1–2. Built on the open home story grid in `templates/available-homes-carousel/story.py`, which matches `stories/sh-07nov2026/stills/00_cover.png`.

| Element | Spec |
|---|---|
| Photo | x0 y0, 1080 × 1040. Use the last home listed on that cover |
| Panel | Stone `#1E1E1E`, y1040–1920 |
| Atlas icon (white) | x60 y1105, 78 × 78 |
| Title | `Open Homes`: Rhymes Text Light 64px white, top 1205 |
| Line | Fakt Medium 27px white caps, tracking 0.15, top 1297: `LOWER NORTH SHORE · SATURDAY 21 NOVEMBER` |
| List | Two columns, x64 and x556, first cap top y1373. Nothing below y1720 |
| Time label | Fakt Medium ~21px caps, tracked, **Sand**, start time only (`10:00AM`). Cap height 14–15px |
| Addresses | Fakt Normal ~30px **white**, street only, one per line. Cap height 22px |
| Rhythm (cap top to cap top) | Label to first address 35px; address to address 40px; last address to next label 58px |
| Fill | Time order, then street. Fill the left column, then the right; never split a time group. About 10 addresses per cover, then make cover 2 of 2 |

Font sizes are approximate, measured from the 21 Nov export.

In Canva the list is a placed image, because Canva's API can't style text line by line. Render it in code, or build it by hand in Canva.

The rental cover line isn't settled. See **Open decisions**.

## OPEN tag

Shared by every format. Matches the 12 Nov Lower North Shore stories.

- **Box:** Terra `#734137`, 125px high, width = widest line + 76 (38px each side), corner radius 4.
- **Text:** Fakt Medium 25px, tracking 5.7px (≈0.23em; Canva letter spacing 150), white, all caps, centred. Line 1 cap top at +32, line 2 at +74 (cap height 18).
- **Line 1:** `OPEN TODAY` on the day, `OPEN SATURDAY` for a future day, or `AUCTION TODAY`.
- **Line 2:** `3:00 – 3:15PM` (en dash with spaces; one AM/PM when both times share it); `11:45AM – 12:15PM` when the range crosses noon.
- The Canva story tags are placed images. Render them with `story_tools.py tag` and composite them in code. Canva's API can't set fonts on new text, so a tag rebuilt in Canva comes out off-brand.

The SH 7 Nov tabs in `stories/sh-07nov2026/tabs/` have 33px each side. Everything else on them matches.

## Instagram safe zones and link sticker

- Nothing important in the top 220px (profile name and progress bar). All text above y1680 (reply bar).
- The link sticker is added in Instagram, not Canva, and links to the atlas.com.au listing. Copy: `OPEN 3:00PM TODAY` or `AUCTION 1:00PM TODAY`.
- The template notes say to put the sticker left-aligned at mid-screen (y≈960). On split cards that covers the baked-in tag, so put it in the white space below the body copy (around y1600).

## Animation

- 3 property photos per home (rooms or outdoor areas of the home itself, no suburb or area shots unless asked), lead photo first.
- Each photo holds 4.5s with a 0.8s crossfade and a slow 6% zoom. 30 fps, about 11.9s in total.
- H.264, yuv420p, CRF 17, `+faststart`, no audio.
- Card text and tag stay still. The tag is composited on every frame.
- Use `--anchor=topleft` when photos carry a burned-in "Virtually staged" label, so the label stays in frame.

## Data and compliance

- **Source of truth:** atlas.com.au.
  - Feed: `https://www.atlas.com.au/___filter?q=<urlencoded JSON>&page=1&perPage=200`, with `{"orderBy":"earliestInspectionDateTime_ASC","filter":{"type":"DatoCmsProperty","for":{"in":["sale"]},"office":{"eq":"N0c5XYyhTX2LH2o7pcWCGQ"}}}`.
  - **The `office` and `for` filters aren't applied server-side.** Filter client-side on `for` (`sale` or `lease`), state (exclude QLD for NSW stories), suburb or region, and `inspections[].inspectionDate` (e.g. `Tuesday 24th November 2026`, with `inspectionTime` and `inspectionEndTime`).
  - Office IDs: Lower North Shore `N0c5XYyhTX2LH2o7pcWCGQ`, Southern Highlands `cgmYO6KbRWmUGd4EXAMmTQ`, Byron Bay `eBJrsZ7fQgy8xQweUgV2ng`.
- **Agent:** listing page `https://www.atlas.com.au/property/<slug>`, in the JSON-LD `"agent":[{"name":…}]`.
- **Body copy:** the first `<p>` of the description on the listing page, word for word.
- **Photos:** from the listing page, `https://images.sales.reapit.com.au/26319/listing/<ID>/photo/d/<n>.jpg?wm=0` (1920 × 1280).
- **Virtual staging:**
  - Never crop out or cover the "Virtually staged" label.
  - Add `Image virtually staged.` after the body copy, because Instagram's interface can cover the label.
  - Say so when the story is handed over.
- No prices or rent on stories. Don't invent claims. Features must match the website.
- Region names: Lower North Shore, Southern Highlands, Byron Bay. NSW stories exclude Brisbane.
- **Network:** needs `www.atlas.com.au`, `images.sales.reapit.com.au` and `export-download.canva.com` (for Canva PNG exports).

## Canva references (duplicate, never edit)

| Design | ID | Use |
|---|---|---|
| PM – Story – Template (duplicate for new rentals) | `DAHZwcAxanc` | Split card, rentals |
| SH – Story – Template (duplicate for new listings) | `DAHZt9DJzXQ` | Split card, sales |
| LNS OFI Stories – Thu 12 Nov 2026 | `DAHbZjk7eOw` | Sent reference; tag style and placement |
| LNS Rental OFI Stories – Tue 24 Nov 2026 (Jaime Pratt) | `DAHbxP96m28` | Latest rental split cards (6/3 Millett Rd, 102/96 Ben Boyd Rd) |
| OFI Story Template Options – film clips – Sat 21 Nov | `DAHbavwou80` | Options A (split), B (full-bleed), C (framed) |
| OFI Stories – Sat 21 Nov 2026 – v2 Option A – DRAFT | `DAHba4SkpF0` | Covers (pages 1–2) |
| DRAFT – Open Home Story – Full Media | `DAHZioRVA_Y` | Headline variant (eyebrow, headline, features, body). Not full-bleed despite the name |

- Canva icon media: dark Atlas icon `MAHLR-grvGA`, white `MAHbalDNFZ4`. For code renders, use `assets/brandmark_mask.png`, or crop the icon from a 1080 × 1920 Canva export.
- **Naming:**
  - Canva: `LNS Rental OFI Stories – Tue 24 Nov 2026 (Agent)`, `OFI Cover – LNS – Sat 21 Nov 2026 (1 of 2)`
  - Files: `Story – <street>, <suburb> – Open <time>.mp4`

## QA before a story goes out

- Every home open on that date is on the site, and no extras. Bed, bath, car and land figures match the listing.
- Copy is word for word, Australian English, singular and plural correct.
- Tag text and time are correct, and the tag sits in the right place.
- Text sits inside the safe zones. Staging labels stay visible.
- Pull frames at 0.3s, the crossfades and the end, and check them side by side with the reference story.
- The MP4 is 1080 × 1920 and about 12s.
