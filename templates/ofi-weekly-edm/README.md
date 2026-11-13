# Weekly OFI email template (all regions)

The Saturday open-homes email for Lower North Shore, Southern Highlands and Byron Bay. It was first sent for Saturday 7 November 2026. `example/OFI_NSW_07Nov2026.html` is that send. It uses the old tile launchpad, so the current build no longer reproduces it exactly: the top section was redesigned on 13 Nov 2026 (see Locked design).

## Build a new week

1. **Data.** Make a `dataset.json` with the keys `LNS`, `STH` and `BYB`. Each one is a list of that region's opens in time order. Copy the fields from `example/dataset-07nov2026.json`: `street`, `suburb`, `spec`, `time`, `start`, `url`, `pid`, `img`, `alt`. Check it against the live upcoming-inspections list on atlas.com.au.
2. **Region images.** Put the tiles in `ofi/<ddmonyyyy>/` in this repo: `tile-lns.jpg`, `tile-sh.jpg` and `tile-byb.jpg` (526 × 350). Then run `python3 make_thumbs.py ../../ofi/<ddmonyyyy>` to make the 2:1 thumbnails the top section uses (`thumb-lns.jpg`, `thumb-sh.jpg`, `thumb-byb.jpg`, 288 × 144). Commit and push them before you send, because the email loads them from jsDelivr.
3. **Build:**
   ```
   python3 build_ofi.py --date 2026-11-14 --data dataset.json
   ```
   This writes `OFI_NSW_14Nov2026.html`. It sets the title tag, the header date ("SATURDAY 14 NOVEMBER"), the UTM campaign dates and the thumbnail links from `--date`. The XHTML pass runs as the last step.
4. **QA:** run `python3 qa/verify_email.py <file>`, then the Playwright checks in `qa/` (`shot.js` takes desktop and mobile screenshots, `final_audit.js` and `btncheck.js` check computed styles). Check colours by sampling pixels, not by looking at screenshots.
5. **Send.** Import into Stripo, then ActiveCampaign. ActiveCampaign adds its own compliance footer, so the template doesn't include one.

## Locked design

- **Top section** (Figma `OFI template`, frames 15:48 desktop and 37:3 mobile):
  - **Header:** dark #20211f, 88px high. The Atlas logo at 140 × 28 sits on the left. On the right are two Fakt Normal caps lines, OPEN HOMES and SATURDAY 14 NOVEMBER, white, 14px with 1px tracking (12px on mobile).
  - **Region list** (white): a Fakt Medium 10px caps eyebrow, "OPEN INSPECTIONS BY REGION", then "Plan your Saturday" in Rhymes Light 36px (32px on mobile). Below that, one row per region in the order Lower North Shore, Southern Highlands, Byron Bay. Each row has a 2:1 thumbnail (144 × 72, or 96 × 48 on mobile), the region name in Rhymes Light 23px (19px on mobile), and the links OPEN HOMES and BY APPOINTMENT.
  - **All regions bar:** a #ebe4df band with ALL REGIONS and the same two links. OPEN HOMES goes to every region's inspections, and BY APPOINTMENT goes to atlas.com.au/contact.
  - **Links:** Fakt Normal caps, 14px with 1px tracking (12px on mobile), #1e1e1e, with a 1px underline drawn as a cell border so it holds in Outlook.
  - The top section replaces the old 2 × 2 tile launchpad and the separate "Plan your Saturday" title band, so Lower North Shore follows the All regions bar directly.
- **Section colours:** Lower North Shore is light sand #EFE9E5, Southern Highlands is white and Byron Bay is #EFE9E5. Never use hairline separators.
- **Section titles:** a Fakt caps label with a Rhymes title only, e.g. "OPEN INSPECTIONS BY REGION" over "Plan your Saturday". Never stack three lines, and never add the globe.
- **Off-market** comes after the regions. REGISTER goes to hq.atlas.com.au/offmarket.
- **Fonts:** Rhymes Display Light (registered at weight 400) and Fakt Normal (400), with Fakt Medium at 500 and 700, all loaded with @font-face from `tadatlas/atlas-app-fonts`. Rhymes falls back to Times and Fakt falls back to Helvetica. Keep Rhymes text at `font-weight: 400`, or clients will fake a bold.

## Content rules

- No prices.
- Where land size is a listing's only feature, show it in place of bed, bath and car (e.g. "763 SQM"). Never show a 0. The build fails if a 0 slips through.
- Leave out 15-minute private appointment slots.
- Use region names (Lower North Shore, Southern Highlands, Byron Bay), never "Sydney" or "NSW".

## Known traps (each one has caused a real defect)

- **Inline backgrounds:** an inline `background-color:#FFFFFF` overrides the `bgcolor` attribute in Outlook. `paint()` sets both and fails if a stray colour is left.
- **Blue dates and times:** Outlook and Apple turn dates and times into blue links. The `.dtl` spans and their CSS stop this.
- **Fat buttons on mobile:** any new button class needs its own mobile CSS rule, or it inherits Stripo's generic padding.
- **Stripo mobile rules:** `.es-content-body p, a` are forced to 14px on mobile, and `.es-table-not-adapt` tables are forced to `width: auto`. The top section uses `lp2-*` classes with scoped mobile rules (`LP2_MOBILE` in `build_ofi.py`), and keeps `es-table-not-adapt` off its full-width tables.
- **Double footer:** don't keep the archive's ActiveCampaign footer table.

## Files

| File | What it is |
| --- | --- |
| `build_ofi.py` | The build script |
| `make_thumbs.py` | Crops the region tiles into the 2:1 thumbnails used in the top section |
| `base_archive.html` | The sent archive of the 31 Oct email. The build reuses its header, footer and section shells |
| `example/` | The 7 Nov dataset and the email it produced |
| `qa/` | The XHTML pass, `verify_email.py` and the Playwright render checks |
