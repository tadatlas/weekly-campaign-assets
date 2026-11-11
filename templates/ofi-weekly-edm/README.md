# Weekly OFI email template (all regions)

The Saturday open-homes email for Lower North Shore, Southern Highlands and Byron Bay. It was first sent for Saturday 7 November 2026. `example/OFI_NSW_07Nov2026.html` is that send, and the build below reproduces it byte for byte.

## Build a new week

1. **Data.** Make a `dataset.json` with the keys `LNS`, `STH` and `BYB`. Each one is a list of that region's opens in time order. Copy the fields from `example/dataset-07nov2026.json`: `street`, `suburb`, `spec`, `time`, `start`, `url`, `pid`, `img`, `alt`. Check it against the live upcoming-inspections list on atlas.com.au.
2. **Tile images.** Upload the four launchpad tiles to `ofi/<ddmonyyyy>/` in this repo: `tile-lns.jpg`, `tile-sh.jpg`, `tile-byb.jpg` and `tile-all.jpg`, each 526 × 350.
3. **Build:**
   ```
   python3 build_ofi.py --date 2026-11-14 --data dataset.json
   ```
   This writes `OFI_NSW_14Nov2026.html`. It sets the title tag, the UTM campaign dates and the tile image links from `--date`. The XHTML pass runs as the last step.
4. **QA:** run `python3 qa/verify_email.py <file>`, then the Playwright checks in `qa/` (`shot.js` takes desktop and mobile screenshots, `final_audit.js` and `btncheck.js` check computed styles). Check colours by sampling pixels, not by looking at screenshots.
5. **Send.** Import into Stripo, then ActiveCampaign. ActiveCampaign adds its own compliance footer, so the template doesn't include one.

## Locked design

- **Launchpad:** the caps label "BROWSE BY REGION", then the Rhymes headline "Open this Saturday," with a smaller second line, "and available by appointment." (desktop 28/22px, mobile 26/19px, second line #5e5e5e).
- **Region tiles:** a 2 × 2 grid, in the order Lower North Shore and Southern Highlands, then Byron Bay and All regions. Each tile has the region name and the links OPEN HOMES and BY APPOINTMENT on one line. Links use the brand's underlined Fakt caps style, the same as VIEW REGION. All regions' BY APPOINTMENT goes to atlas.com.au/contact.
- **Section colours:** a 12px #F5F5F5 band under the launchpad. The title block and Lower North Shore are light sand #EFE9E5, Southern Highlands is white and Byron Bay is #EFE9E5. Never use hairline separators.
- **Section titles:** a Fakt caps label with a Rhymes title only, e.g. "OPEN INSPECTIONS BY REGION" over "Plan your Saturday". Never stack three lines, and never add the globe.
- **Off-market** comes after the regions. REGISTER goes to hq.atlas.com.au/offmarket.
- **Fonts:** Rhymes and Fakt loaded with @font-face, falling back to Times and Helvetica.

## Content rules

- No prices.
- Where land size is a listing's only feature, show it in place of bed, bath and car (e.g. "763 SQM"). Never show a 0. The build fails if a 0 slips through.
- Leave out 15-minute private appointment slots.
- Use region names (Lower North Shore, Southern Highlands, Byron Bay), never "Sydney" or "NSW".

## Known traps (each one has caused a real defect)

- **Inline backgrounds:** an inline `background-color:#FFFFFF` overrides the `bgcolor` attribute in Outlook. `paint()` sets both and fails if a stray colour is left.
- **Blue dates and times:** Outlook and Apple turn dates and times into blue links. The `.dtl` spans and their CSS stop this.
- **Fat buttons on mobile:** any new button class needs its own mobile CSS rule, or it inherits Stripo's generic padding. The tiles use `.lp-links`.
- **Double footer:** don't keep the archive's ActiveCampaign footer table.

## Files

| File | What it is |
| --- | --- |
| `build_ofi.py` | The build script |
| `base_archive.html` | The sent archive of the 31 Oct email. The build reuses its header, footer and section shells |
| `example/` | The 7 Nov dataset and the email it produced |
| `qa/` | The XHTML pass, `verify_email.py` and the Playwright render checks |
