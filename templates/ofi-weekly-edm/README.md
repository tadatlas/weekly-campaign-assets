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

- **Top section** (Figma `OFI template`, frames 15:48 desktop and 37:3 mobile, set to the email's type scale below):
  - **Header:** #1e1e1e (the same near-black as the footer), 88px high. The Atlas logo (140 × 28) sits on the left. The right has OPEN HOMES and SATURDAY 14 NOVEMBER in the caps style.
  - **Region list** (white): the eyebrow "OPEN INSPECTIONS BY REGION", then "Plan your Saturday" in Rhymes Light 36px (32px on mobile). Then one row per region in the order Lower North Shore, Southern Highlands, Byron Bay. Each row has a 2:1 thumbnail (144 × 72 on desktop, 80 × 40 on mobile), the region name in Rhymes Light 22px (18px on mobile), and the OPEN HOMES and BY APPOINTMENT links.
  - **Narrow phones:** below 375px the thumbnails are hidden so the two links stay on one line.
  - **All regions bar:** light sand #EFE9E5, with the label ALL and the same two links on one row at every width. The label is ALL rather than ALL REGIONS so the row fits on a 360px phone. OPEN HOMES goes to every region's inspections, and BY APPOINTMENT goes to atlas.com.au/contact.
  - **Links:** the caps style, with a 0.5px #1e1e1e underline 5px below the text. Every link underline in the email, VIEW REGION included, is 0.5px. The underline is drawn as a cell border so it holds in Outlook.
- **Type scale** (one style per role, the same on desktop and mobile unless noted):
  - Rhymes Light, weight 400: headline 36px (mobile 32px); off-market title 28px (mobile 26px); region names 22px (mobile 18px), the same in the top list and the section headers; street names 18px (mobile 16px).
  - Fakt Normal, weight 400: caps labels and links are 11px with 2px tracking at every width. That covers the eyebrows, VIEW REGION, OPEN HOMES, BY APPOINTMENT, ALL, REGISTER, suburbs, specs, OPEN INSPECTION and the header. Times are 12px.
  - All text in the content sections is #1e1e1e. The footer keeps its own smaller sizes.
- **Property cards:** each pair of cards is one table with a row per element (image, street, suburb, specs, OPEN INSPECTION, time). A street name that wraps makes the whole row taller, so both cards in the pair always line up. On mobile the two columns share the width equally, with a 12px gap made from padding on each card. A separate gap cell would be squeezed to nothing between two 50% columns.
- **One line per copy line:** no card line may wrap, at any width down to a 360px phone (where each card column is 149px). The build shortens the copy to fit:
  - Times use "Sat" ("Sat 11:00am – 11:30am").
  - Street types are abbreviated (Street → St, Road → Rd, Crescent → Cres and so on).
  - Suburbs drop " NSW".
  - If a street name is still too long, the build prints a warning. Add `"street_short"` to that property in the dataset (e.g. "71/2-18 Centennial Rd" for "Villa 71/2-18 Centennial Road").
  - As a safety net, mobile cuts any line that still overflows with "…" rather than wrapping it.
- **Section colours:** after the top section, the sections alternate, starting with white: Lower North Shore is white, Southern Highlands is light sand #EFE9E5, and Byron Bay is white. Off-market keeps its dark panel. Use one sand only (#EFE9E5). Never use hairline separators.
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
- **Gmail drops big or unsupported style blocks:** the Gmail apps ignore any `<style>` over about 16 KB, or any block with an attribute selector, an id or a `*` wildcard. The archive's CSS was one 43 KB block, so on Gmail mobile the desktop layout showed, shrunk. The build now writes Gmail-safe CSS (`gmail_safe_style_blocks`): duplicates removed, `X *` rewritten as `X a, X span, X strong`, the Apple and Samsung fixes in their own small block, and every block under 15 KB. It also strips the inline `var(--…)` dark-mode layer. Non-Gmail accounts opened in the Gmail app never get mobile CSS.
- **Gmail auto-links addresses:** the Gmail app can turn a street plus suburb into one map link and fold the lines below into it. With the one-line rule, that hid a card's suburb, specs and time (26 Redan St and Ave Rd, 14 Nov). Street names are now links to their listing (class `ofi-street`). Gmail doesn't auto-link text that's already a link.
- **Gmail clips at about 102 KB:** a full week (about 45 cards) is around 280 KB, so Gmail shows roughly the first 16 cards and then a "View entire message" link. Getting under the limit means rebuilding the card markup.
- **Double footer:** don't keep the archive's ActiveCampaign footer table.
- **No unsubscribe in the template:** ActiveCampaign adds its own, so the build drops the footer's plain-text UNSUBSCRIBE line. PRIVACY POLICY links to atlas.com.au/privacy-policy. The social links match the atlas.com.au footer: facebook.com/atlassydneyandeastcoast, instagram.com/atlas_sydney_eastcoast and linkedin.com/company/atlas-realestate-au.

## Files

| File | What it is |
| --- | --- |
| `build_ofi.py` | The build script |
| `make_thumbs.py` | Crops the region tiles into the 2:1 thumbnails used in the top section |
| `base_archive.html` | The sent archive of the 31 Oct email. The build reuses its header, footer and section shells |
| `example/` | The 7 Nov dataset and the email it produced |
| `qa/` | The XHTML pass, `verify_email.py` and the Playwright render checks |
