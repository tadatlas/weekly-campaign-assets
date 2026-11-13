#!/usr/bin/env python3
"""Build the weekly all-regions OFI email.

Usage:
    python3 build_ofi.py --date 2026-11-14 --data dataset.json [--out OFI_NSW_14Nov2026.html]

--date  the Saturday of the opens (YYYY-MM-DD)
--data  JSON with keys LNS, STH, BYB: lists of open homes in time order
        (see example/dataset-07nov2026.json for the fields)
"""
import argparse, datetime, json, os, re, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ap = argparse.ArgumentParser()
ap.add_argument("--date", required=True)
ap.add_argument("--data", required=True)
ap.add_argument("--out")
args = ap.parse_args()
SAT = datetime.date.fromisoformat(args.date)
ARCHIVE = os.path.join(HERE, "base_archive.html")
DATA = args.data
OUT = args.out or f"OFI_NSW_{SAT.strftime('%d%b%Y')}.html"
TITLE_DATE = f"{SAT.day} {SAT.strftime('%B')}"

src = open(ARCHIVE, encoding="utf-8", errors="replace").read()
data = json.load(open(DATA))

DATE = SAT.strftime("%d%b%Y").lower()
CDN = f"https://cdn.jsdelivr.net/gh/tadatlas/weekly-campaign-assets@main/ofi/{DATE}"
BASE_UTM = "utm_source=ofi_edm&utm_medium=email"
REG_SLUG = {"LNS": "lns", "STH": "southern_highlands", "BYB": "byron_bay"}
INSPECT = {
    "LNS": "https://www.atlas.com.au/upcoming-inspections?queryType=inspection&forType=sale&office=N0c5XYyhTX2LH2o7pcWCGQ&sort=earliestInspectionDateTime_ASC&page=1",
    "STH": "https://www.atlas.com.au/upcoming-inspections?queryType=inspection&forType=sale&office=cgmYO6KbRWmUGd4EXAMmTQ&sort=earliestInspectionDateTime_ASC&page=1",
    "BYB": "https://www.atlas.com.au/upcoming-inspections?queryType=inspection&forType=sale&office=eBJrsZ7fQgy8xQweUgV2ng&sort=earliestInspectionDateTime_ASC&page=1",
}
OFFICE = {
    "LNS": "https://www.atlas.com.au/office/lower-north-shore",
    "STH": "https://www.atlas.com.au/office/southern-highlands",
    "BYB": "https://www.atlas.com.au/office/byron-bay",
}
ALL_INSPECT = "https://www.atlas.com.au/upcoming-inspections?queryType=inspection&forType=sale&sort=earliestInspectionDateTime_ASC"
ALL_APPT = "https://www.atlas.com.au/contact"
OFFMARKET = "https://hq.atlas.com.au/offmarket"

def utm(url, campaign, content):
    sep = "&" if "?" in url else "?"
    return f"{url}{sep}{BASE_UTM}&utm_campaign=weekly_ofi_{campaign}_{DATE}&utm_content={content}"

# ---------- 1. carve the email out of the archive page ----------
w = src.find('<div dir="ltr" lang="en" class="es-wrapper-color"')
badge = src.find('Email Marketing</a> by ActiveCampaign')
assert w > 0 and badge > w
wrap_close = src.find('<br clear="all" /></div>', w, badge)
assert wrap_close > 0
body = src[w:wrap_close].rstrip()  # wrapper div + trailing es-footer table; the br/div is archive chrome
assert body.count("<table") == body.count("</table>"), "unbalanced tables in body slice"
assert body.count("<div") == body.count("</div>"), "unbalanced divs in body slice"

styles = []
for m in re.finditer(r"<style[^>]*>", src):
    b = src.find("</style>", m.end())
    content = src[m.end():b]
    if ".es-" in content or content.strip().startswith(("a {", "sup")):
        styles.append(src[m.start():b + len("</style>")])
assert len(styles) == 3, f"expected 3 email style blocks, got {len(styles)}"

# ---------- 2. section offsets inside body ----------
cts = [m.start() for m in re.finditer(r'<table[^>]*class="es-content"', body)]
assert len(cts) == 5, cts
ftr = body.find('<table', body.rfind('class="es-footer"') - 200)
ftr = [m.start() for m in re.finditer(r'<table[^>]*class="es-footer"', body)][0]
seg = {}
bounds = cts + [ftr]
names = ["tiles", "offm", "LNS", "SH", "BYB"]
for i, n in enumerate(names):
    seg[n] = body[bounds[i]:bounds[i + 1]]
head_part = body[:bounds[0]]          # wrapper open + es-header
foot_part = body[ftr:]                # es-footer + wrapper close

# ---------- 3. helpers ----------
def tr_block(s, start):
    """return end index of balanced <tr> starting at `start`"""
    depth = 0
    for m in re.finditer(r"<tr\b|</tr>", s[start:]):
        depth += 1 if m.group(0) != "</tr>" else -1
        if depth == 0:
            return start + m.end()
    raise ValueError("unbalanced tr")

def row_tds(s):
    return [m.start() for m in re.finditer(r'<td[^>]*class="[^"]*es-module-(?:8275|9157)[^"]*"', s)]

def split_section(s):
    tds = row_tds(s)
    starts = [s.rfind("<tr>", 0, t) for t in tds]
    last_end = tr_block(s, starts[-1])
    return s[:starts[0]], [s[a:tr_block(s, a)] for a in starts], s[last_end:]

lns_head, lns_rows, lns_tail = split_section(seg["LNS"])
sh_head, sh_rows, sh_tail = split_section(seg["SH"])
byb_head, byb_rows, byb_tail = split_section(seg["BYB"])

ROW = lns_rows[0]
SPLITTER = '<td class="es-m-w0 es-m-p10r"'
left_raw, right_raw = ROW.split(SPLITTER)
right_raw = SPLITTER + right_raw

def tokenize(chunk, street, suburb, spec, time):
    c = chunk
    c = re.sub(r'href="[^"]*lt\.php[^"]*"', 'href="{HREF}"', c, count=1)
    c = re.sub(r'src="[^"]*"', 'src="{IMG}"', c, count=1)
    c = re.sub(r'alt="[^"]*"', 'alt="{ALT}"', c, count=1)
    for old, tok in [(street, "{STREET}"), (suburb, "{SUBURB}"), (spec, "{SPEC}"), (time, "{TIME}")]:
        assert old in c, old
        c = c.replace(f">{old}<", f">{tok}<")
    return c

LEFT_T = tokenize(left_raw, "34 Jeffreys Street", "KIRRIBILLI NSW",
                  "4 BED &nbsp;4 BATH &nbsp;2 CAR", "Saturday 9:15am – 9:45am")
RIGHT_T = tokenize(right_raw, "11/34-40 Union Street", "MCMAHONS POINT NSW",
                   "3 BED &nbsp;3 BATH &nbsp;2 CAR", "Saturday 10:00am – 10:30am")

def fill(tpl, p, region):
    href = utm(p["url"], REG_SLUG[region], p["pid"])
    return (tpl.replace("{HREF}", href).replace("{IMG}", p["img"])
               .replace("{ALT}", p["alt"].replace('"', ""))
               .replace("{STREET}", p["street"]).replace("{SUBURB}", p["suburb"])
               .replace("{SPEC}", p["spec"])
               .replace("{TIME}", f'<span class="dtl">{p["time"]}</span>'))

# empty right column: keep structure, blank the presentation table
pt = right_raw.find('role="presentation"')
pt_open_end = right_raw.find(">", right_raw.rfind("<table", 0, pt)) + 1
pt_close = right_raw.find("</table>", pt_open_end)
EMPTY_RIGHT = (right_raw[:pt_open_end]
               + '<tr><td style="padding: 0; Margin: 0; font-size: 0; line-height: 0">&nbsp;</td></tr>'
               + right_raw[pt_close:])

def last_variant(row):
    row = row.replace("es-m-p25b es-module-8275", "es-m-p50b es-module-9157")
    return row.replace("padding: 15px 30px", "padding: 15px 30px 60px")

def build_rows(props, region):
    rows, i = [], 0
    while i < len(props):
        l = fill(LEFT_T, props[i], region)
        if i + 1 < len(props):
            r = fill(RIGHT_T, props[i + 1], region)
        else:
            r = EMPTY_RIGHT
        rows.append(l + r)
        i += 2
    rows[-1] = last_variant(rows[-1])
    return "".join(rows)

def swap_lt(block, url):
    return re.sub(r'https://iq\.atlas\.com\.au/lt\.php\?x=[^"]*', url, block, count=1)

def set_bg(block, color):
    block = re.sub(r'(class="es-content-body"[^>]*background-color: )#[0-9a-fA-F]{6}', r"\1" + color, block)
    block = re.sub(r'bgcolor="#[0-9a-fA-F]{6}"( class="es-content-body")', f'bgcolor="{color}"\\1', block)
    # attribute order variant: bgcolor before class
    block = re.sub(r'(<table[^>]*bgcolor=")#[0-9a-fA-F]{6}("[^>]*class="es-content-body")', r"\1" + color.lstrip("#") and r"\g<1>" + color[1:] + r"\g<2>", block)
    return block

LIGHT_SAND = "#efe9e5"

# region sections
lns_head2 = swap_lt(lns_head, utm(INSPECT["LNS"], "lns", "view_region"))
sh_head2 = swap_lt(sh_head, utm(INSPECT["STH"], "southern_highlands", "view_region"))
byb_head2 = swap_lt(byb_head, utm(INSPECT["BYB"], "byron_bay", "view_region"))

def paint(block, color):
    """recolour the section's es-content-body table tag (attrs in any order).
    Handles any spacing after the colon, and guarantees BOTH a bgcolor
    attribute and a style background-color so every client gets the colour."""
    m = re.search(r'<table[^>]*class="es-content-body"[^>]*>', block)
    assert m, "no es-content-body in block"
    tag = m.group(0)
    new = re.sub(r'bgcolor="#[0-9a-fA-F]{3,6}"', f'bgcolor="{color}"', tag)
    new = re.sub(r"background(-color)?:\s*#[0-9a-fA-F]{3,6}",
                 lambda mm: ("background-color" if mm.group(1) else "background") + ": " + color, new)
    if 'bgcolor="' not in new:
        new = new.replace("<table ", f'<table bgcolor="{color}" ', 1)
    if "background-color" not in new:
        new = new.replace('style="', f'style="background-color: {color}; ', 1)
    # no stale hex of any other colour may remain in this tag
    leftover = [h for h in re.findall(r"#[0-9a-fA-F]{3,6}", new) if h.lower() != color.lower()]
    assert not leftover, f"unpainted colour left in tag: {leftover} // {new}"
    return block.replace(tag, new, 1)

lns_head2 = paint(lns_head2, LIGHT_SAND)
sh_head2 = paint(sh_head2, "#ffffff")
byb_head2 = paint(byb_head2, LIGHT_SAND)

LNS_SEC = lns_head2 + build_rows(data["LNS"], "LNS") + lns_tail
SH_SEC = sh_head2 + build_rows(data["STH"], "STH") + sh_tail
BYB_SEC = byb_head2 + build_rows(data["BYB"], "BYB") + byb_tail

# ---------- 4. top section: brand header + region list (Figma "OFI template" 15:48 desktop, 37:3 mobile) ----------
t0 = seg["tiles"]
cb = t0.find('class="es-content-body"')
first_tr = t0.find("<tr>", t0.find(">", cb))
open0 = t0[:first_tr]
close0 = lns_tail  # same closing structure for every es-content table

INK = "#1e1e1e"
HEADER_BG = "#20211f"
ALL_BG = "#ebe4df"
# Rhymes Light is registered at weight 400, Fakt Normal at 400 and Fakt Medium at 500
# (see FONT_CSS). Every stack falls back to Times / Helvetica.
RHYMES = "'Rhymes Display', 'times new roman', times, baskerville, georgia, serif"
FAKT = "Fakt, helvetica, 'helvetica neue', arial, verdana, sans-serif"
LOGO = ("https://eupsscf.stripocdn.email/content/guids/CABINET_399e3ce7c0233178f8ffdcf5f73b4ebe7cc6aec5daeb767c90c6e81e04368330"
        "/images/atlas_logo_combined2.png")
NT = 'role="presentation" cellpadding="0" cellspacing="0" border="0" class="es-table-not-adapt"'
NTW = 'role="presentation" cellpadding="0" cellspacing="0" border="0"'  # full-width: Stripo keeps these at 100%
TBL = "border-collapse: collapse; border-spacing: 0px; mso-table-lspace: 0pt; mso-table-rspace: 0pt"

def fakt_p(text, cls, size, color=INK, weight=400, track="1px", lh=None, align="left"):
    lh = lh or f"{round(size * 1.5)}px"
    return (f'<p class="{cls}" style="Margin: 0; mso-line-height-rule: exactly; font-family: {FAKT}; '
            f'font-size: {size}px; line-height: {lh}; letter-spacing: {track}; font-weight: {weight}; '
            f'font-style: normal; text-transform: uppercase; color: {color}; text-align: {align}">{text}</p>')

def rhymes_p(text, cls, size, track="0"):
    return (f'<p class="{cls}" style="Margin: 0; mso-line-height-rule: exactly; font-family: {RHYMES}; '
            f'font-size: {size}px; line-height: {round(size * 1.15)}px; letter-spacing: {track}; '
            f'font-weight: 400; font-style: normal; color: {INK}">{text}</p>')

def ulink(text, href):
    """Fakt caps link with the underline drawn as a cell border (Outlook ignores borders on <a>)."""
    return (f'<td class="lp2-u" style="padding: 0 0 1px; Margin: 0; border-bottom: 1px solid {INK}; white-space: nowrap">'
            f'<a href="{href}" target="_blank" class="lp2-link" style="mso-line-height-rule: exactly; '
            f'font-family: {FAKT}; font-size: 14px; line-height: 21px; letter-spacing: 1px; font-weight: 400; '
            f'text-transform: uppercase; text-decoration: none; color: {INK}; white-space: nowrap">{text}</a></td>')

def link_pair(h1, h2):
    return (f'<table {NT} style="{TBL}"><tr>{ulink("OPEN HOMES", h1)}'
            f'<td class="lp2-lgap" width="24" style="width: 24px; padding: 0; Margin: 0; font-size: 0; line-height: 0">&nbsp;</td>'
            f'{ulink("BY APPOINTMENT", h2)}</tr></table>')

# -- brand header: logo left, OPEN HOMES / SATURDAY 14 NOVEMBER right --
hdr_i = head_part.find('class="es-module-4556')
assert hdr_i > 0, "brand header cell not found"
hdr_tr = head_part.rfind("<tr>", 0, hdr_i)
hdr_end = tr_block(head_part, hdr_tr)
assert "THIS WEEKEND" in head_part[hdr_tr:hdr_end]
SAT_LABEL = f"SATURDAY {SAT.day} {SAT.strftime('%B').upper()}"
HEADER_TR = (
    f'<tr><td align="left" bgcolor="{HEADER_BG}" class="lp2-hdr" style="Margin: 0; background-color: {HEADER_BG}; padding: 23px 30px">'
    f'<table {NTW} width="100%" style="{TBL}; width: 100%"><tr>'
    f'<td align="left" valign="middle" style="padding: 0; Margin: 0; font-size: 0; line-height: 0">'
    f'<img src="{LOGO}" width="140" height="28" alt="Atlas" style="display: block; border: 0; outline: none; text-decoration: none; width: 140px; height: 28px; font-size: 14px; color: #ffffff" /></td>'
    f'<td align="right" valign="middle" style="padding: 0; Margin: 0">'
    + fakt_p("OPEN HOMES", "lp2-hdr-t", 14, "#ffffff", align="right")
    + fakt_p(f'<span class="dtl">{SAT_LABEL}</span>', "lp2-hdr-t", 14, "#ffffff", align="right")
    + '</td></tr></table></td></tr>')
head_part = head_part[:hdr_tr] + HEADER_TR + head_part[hdr_end:]

# -- region list --
THUMB = {"LNS": "lns", "STH": "sh", "BYB": "byb"}
REGION_NAME = {"LNS": "Lower North Shore", "STH": "Southern Highlands", "BYB": "Byron Bay"}

def region_row(key):
    slug = REG_SLUG[key]
    img = f"{CDN}/thumb-{THUMB[key]}.jpg"
    h_img = utm(OFFICE[key], slug, "tile_image")
    return (
        f'<tr><td class="lp2-row" style="padding: 20px 0; Margin: 0">'
        f'<table {NTW} width="100%" style="{TBL}; width: 100%"><tr>'
        f'<td class="lp2-thumb" width="144" valign="middle" style="width: 144px; padding: 0; Margin: 0; font-size: 0; line-height: 0">'
        f'<a href="{h_img}" target="_blank"><img src="{img}" width="144" height="72" alt="{REGION_NAME[key]}" class="lp2-img" '
        f'style="display: block; border: 0; outline: none; text-decoration: none; width: 144px; height: 72px" /></a></td>'
        f'<td class="lp2-gap" width="24" style="width: 24px; padding: 0; Margin: 0; font-size: 0; line-height: 0">&nbsp;</td>'
        f'<td valign="middle" style="padding: 0; Margin: 0">'
        + rhymes_p(REGION_NAME[key], "lp2-name", 23)
        + f'<table {NT} style="{TBL}"><tr><td class="lp2-ngap" height="14" style="height: 14px; padding: 0; Margin: 0; font-size: 0; line-height: 0">&nbsp;</td></tr></table>'
        + link_pair(utm(INSPECT[key], slug, "open_homes"), utm(OFFICE[key], slug, "by_appointment"))
        + '</td></tr></table></td></tr>')

LIST_TR = (
    f'<tr><td align="left" class="lp2-pad" style="padding: 40px 30px 20px; Margin: 0">'
    + fakt_p("OPEN INSPECTIONS BY REGION", "lp2-eyebrow", 10, weight=500, track="1.5px", lh="14px")
    + f'<table {NT} style="{TBL}"><tr><td height="12" style="height: 12px; padding: 0; Margin: 0; font-size: 0; line-height: 0">&nbsp;</td></tr></table>'
    + rhymes_p("Plan your Saturday", "lp2-title", 36, "-0.7px")
    + f'<table {NTW} width="100%" style="{TBL}; width: 100%; Margin-top: 20px">'
    + region_row("LNS") + region_row("STH") + region_row("BYB")
    + '</table></td></tr>')

ALL_TR = (
    f'<tr><td align="left" bgcolor="{ALL_BG}" class="lp2-all" style="background-color: {ALL_BG}; padding: 10px 30px; Margin: 0">'
    f'<table {NT.replace("es-table-not-adapt", "es-table-not-adapt lp2-all-in")} style="{TBL}; Margin: 0"><tr>'
    f'<td class="lp2-all-lbl" width="144" height="36" align="center" valign="middle" style="width: 144px; height: 36px; padding: 0; Margin: 0; white-space: nowrap">'
    + fakt_p("ALL REGIONS", "lp2-all-t", 14, align="center")
    + f'</td><td class="lp2-gap" width="24" style="width: 24px; padding: 0; Margin: 0; font-size: 0; line-height: 0">&nbsp;</td>'
    f'<td valign="middle" style="padding: 0; Margin: 0">'
    + link_pair(utm(ALL_INSPECT, "all_regions", "open_homes"), utm(ALL_APPT, "all_regions", "by_appointment"))
    + '</td></tr></table></td></tr>')

lp = paint(open0, "#ffffff") + LIST_TR + ALL_TR + close0

# Mobile sizes from the 375px frame (37:3). Selectors are scoped to beat Stripo's
# generic ".es-content-body p / a { font-size: 14px !important }" and "p, a { line-height: 150% }".
LP2_MOBILE = """@media only screen and (max-width:600px) {
 .es-header-body td.lp2-hdr { padding: 23px 20px !important }
 .es-header-body p.lp2-hdr-t { font-size: 12px !important; line-height: 18px !important }
 .es-content-body td.lp2-pad { padding: 32px 20px 24px !important }
 .es-content-body p.lp2-title { font-size: 32px !important; line-height: 37px !important }
 .es-content-body p.lp2-eyebrow { font-size: 10px !important; line-height: 14px !important }
 .es-content-body td.lp2-row { padding: 16px 0 !important }
 .es-content-body td.lp2-thumb { width: 96px !important }
 .es-content-body img.lp2-img { width: 96px !important; height: 48px !important }
 .es-content-body td.lp2-gap { width: 16px !important }
 .es-content-body p.lp2-name { font-size: 19px !important; line-height: 22px !important }
 .es-content-body td.lp2-ngap { height: 5px !important }
 .es-content-body a.lp2-link { font-size: 12px !important; line-height: 18px !important }
 .es-content-body td.lp2-lgap { width: 20px !important }
 .es-content-body td.lp2-all { padding: 4px 20px !important }
 .es-content-body table.lp2-all-in { Margin: 0 auto !important }
 .es-content-body td.lp2-all-lbl { width: auto !important; height: 44px !important }
 .es-content-body p.lp2-all-t { font-size: 12px !important; line-height: 18px !important; white-space: nowrap !important }
}"""

# ---------- 5. off-market ----------
offm = swap_lt(seg["offm"], utm(OFFMARKET, "all_regions", "offmarket_register"))
# drop the globe row: the approved layout pairs the caps label + Rhymes title only
gi = offm.find("CABINET_6787")
assert gi > 0
g_tr = offm.rfind("<tr>", 0, gi)
offm = offm[:g_tr] + offm[tr_block(offm, g_tr):]
assert "CABINET_6787" not in offm

# ---------- 6. footer link fixes ----------
foot = foot_part
for url in ["https://www.facebook.com/atlassydneyandeastcoast",
            "https://www.instagram.com/atlas_sydney_eastcoast",
            "https://www.linkedin.com/company/atlas-realestate-au"]:
    foot = swap_lt(foot, url)
# drop the trailing compliance footer — it is ActiveCampaign's auto-appended
# block captured in the archive; AC adds its own fresh one at send time
aci = foot.find('class="es-footer ac-footer"')
assert aci > 0
foot = foot[:foot.rfind("<table", 0, aci)].rstrip()
assert "unsubscribe/2" not in foot and "_t.e.s.t_" not in foot

# ---------- 7. assemble ----------
# foot_part = dark Atlas footer (inside wrapper) + wrapper close + AC compliance footer
new_body = head_part + lp + LNS_SEC + SH_SEC + BYB_SEC + offm + foot

big = styles[-1] if ".es-" in styles[-1] else None
assert big and "@media" in big
styles[-1] = styles[-1].replace("@media", "@media only screen and (max-width:600px) { .ofi-heading-wrap { white-space: normal !important } }\n@media", 1)
# top section mobile sizes
styles[-1] = styles[-1].replace("@media", LP2_MOBILE + "\n@media", 1)

# neutralise auto-detected date/time links (Outlook iOS, Apple Mail turn them blue)
DTL = (".dtl a, .dtl a:link, .dtl a:visited, a[x-apple-data-detectors] "
       "{ color: inherit !important; text-decoration: none !important; "
       "font-size: inherit !important; font-family: inherit !important; "
       "font-weight: inherit !important; line-height: inherit !important; }")
m0 = re.search(r"<style[^>]*>", styles[-1])
styles[-1] = styles[-1][:m0.end()] + "\n" + DTL + "\n" + styles[-1][m0.end():]

# ---------- brand fonts: Rhymes + Fakt, falling back to Times / Helvetica ----------
FCDN = "https://cdn.jsdelivr.net/gh/tadatlas/atlas-app-fonts@main"
FONT_CSS = f"""<style type="text/css">
@font-face {{ font-family: 'Rhymes Display'; font-style: normal; font-weight: 400;
  src: url('{FCDN}/rhymes%20woff/Rhymes%20Display%20Light.woff2') format('woff2'),
       url('{FCDN}/rhymes%20woff/Rhymes%20Display%20Light.woff') format('woff'); }}
@font-face {{ font-family: 'Fakt'; font-style: normal; font-weight: 400;
  src: url('{FCDN}/Fakt%20WOFF/FaktTT-Normal.woff2') format('woff2'),
       url('{FCDN}/Fakt%20WOFF/FaktTT-Normal.woff') format('woff'); }}
@font-face {{ font-family: 'Fakt'; font-style: normal; font-weight: 500;
  src: url('{FCDN}/Fakt%20WOFF/FaktTT-Medium.woff2') format('woff2'),
       url('{FCDN}/Fakt%20WOFF/FaktTT-Medium.woff') format('woff'); }}
@font-face {{ font-family: 'Fakt'; font-style: normal; font-weight: 700;
  src: url('{FCDN}/Fakt%20WOFF/FaktTT-Medium.woff2') format('woff2'),
       url('{FCDN}/Fakt%20WOFF/FaktTT-Medium.woff') format('woff'); }}
</style>"""

def brandify(html):
    html = re.sub(r"(?<!'Rhymes Display', )'times new roman', times, baskerville, georgia, serif",
                  "'Rhymes Display', 'times new roman', times, baskerville, georgia, serif", html)
    html = re.sub(r"(?<!Fakt, )helvetica, 'helvetica neue', arial, verdana,",
                  "Fakt, helvetica, 'helvetica neue', arial, verdana,", html)
    return html

new_body = brandify(new_body)
styles = [brandify(x) for x in styles]

doc = f"""<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<meta http-equiv="X-UA-Compatible" content="IE=edge" />
<meta name="x-apple-disable-message-reformatting" />
<title>{TITLE_DATE} Weekly OFI Email</title>
{FONT_CSS}
{styles[0]}
{styles[1]}
{styles[2]}
</head>
<body class="body" style="width:100%;height:100%;padding:0;Margin:0">
{new_body}
</body>
</html>
"""

assert new_body.count("<div") == new_body.count("</div>"), (new_body.count("<div"), new_body.count("</div>"))

# ---------- 8. checks ----------
assert "lt.php" not in doc, "tracking link left behind"
N = sum(len(data[k]) for k in ("LNS", "STH", "BYB"))
pids = re.findall(r"utm_content=(1p\d+)", doc)
assert len(set(pids)) == N, (len(set(pids)), N)
for must in ["Plan your Saturday", "OPEN INSPECTIONS BY REGION", "ALL REGIONS", "hq.atlas.com.au/offmarket",
             f"SATURDAY {SAT.day} {SAT.strftime('%B').upper()}", "thumb-lns.jpg", "thumb-sh.jpg", "thumb-byb.jpg"]:
    assert must in doc, must
for k in ("LNS", "STH", "BYB"):
    for p in data[k]:
        assert p["street"] in doc, p["street"]
        assert not re.search(r"(^|\s)0 (BED|BATH|CAR)", p["spec"]), p["street"]
assert "OPEN TODAY" not in doc

open(OUT, "w", encoding="utf-8").write(doc)
print("written", OUT, len(doc), "bytes")
print("tables balanced:", doc.count("<table") == doc.count("</table>"), doc.count("<table"))
print("divs:", doc.count("<div"), doc.count("</div>"))

# ---------- 9. XHTML pass (Stripo importer needs strict XML) — always the last step ----------
import subprocess
subprocess.run([sys.executable, os.path.join(HERE, "qa", "xhtml_pass.py"), OUT], check=True)
