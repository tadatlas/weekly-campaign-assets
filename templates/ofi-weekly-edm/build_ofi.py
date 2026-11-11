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

# ---------- 4. title band + launchpad from the tiles segment ----------
t0 = seg["tiles"]
cb = t0.find('class="es-content-body"')
first_tr = t0.find("<tr>", t0.find(">", cb))
open0 = t0[:first_tr]
title_tr = t0[first_tr:tr_block(t0, first_tr)]
assert "Plan your Saturday" in title_tr

close0 = lns_tail  # same closing structure for every es-content table

# title band (light sand, sits directly above LNS)
band = paint(open0, LIGHT_SAND) + title_tr + close0
# tighten: band keeps 60px top; LNS header drops from 60px to 30px top
LNS_SEC = LNS_SEC.replace("padding: 60px 30px 15px", "padding: 30px 30px 15px", 1)

# launchpad
caps_p = re.search(r'<p class="es-text-mobile-size-11"[^>]*>', title_tr).group(0)
title_p = re.search(r'<p class="es-m-lh-12 es-text-mobile-size-26"[^>]*>', title_tr).group(0)
lp_title_tr = (title_tr.replace(">OPEN INSPECTIONS BY REGION<", ">BROWSE BY REGION<")
               .replace(">Plan your Saturday<",
                        '><span class="dtl">Open this Saturday,</span><'))
SUB_P = ('<p class="lp-sub" style="mso-line-height-rule: exactly; font-family: \'times new roman\', times, baskerville, georgia, serif; '
         'line-height: 26px; letter-spacing: 0; font-weight: normal; color: #5e5e5e; font-size: 22px; Margin: 0">'
         '<span class="dtl">and available by appointment.</span></p>')
lp_title_tr = lp_title_tr.replace('Open this Saturday,</span></p>', 'Open this Saturday,</span></p>' + SUB_P, 1)
assert SUB_P in lp_title_tr

name_p_m = re.search(r'<p class="es-text-mobile-size-18"[^>]*>', lns_head)
assert name_p_m
NAME_P = name_p_m.group(0)

btn_m = re.search(r'<span class="es-button-border".*?</span>', lns_head, re.S)
assert btn_m
BTN = btn_m.group(0)

def make_btn(text, href):
    b = re.sub(r'href="[^"]*"', f'href="{href}"', BTN, count=1)
    return re.sub(r">\s*VIEW REGION\s*</a>", f"> {text}\n</a>", b)

IMG_TR_L = re.search(r"<tr><td align=\"center\".*?</tr>", left_raw.replace("\n", "\u0001"), re.S)
# simpler: rebuild tile inner rows from scratch using card snippets
img_a_l = re.search(r'<a href[^>]*>\s*<img[^>]*/>\s*</a>', left_raw, re.S).group(0)
img_a_r = re.search(r'<a href[^>]*>\s*<img[^>]*/>\s*</a>', right_raw, re.S).group(0)
gap15 = '<tr><td align="center" height="15" style="padding: 0; Margin: 0"></td></tr>'
gap10 = '<tr><td align="center" height="10" style="padding: 0; Margin: 0"></td></tr>'

def tile_cell(base_chunk, img_a, img_url, alt, name, btn1, btn2):
    pt = base_chunk.find('role="presentation"')
    open_end = base_chunk.find(">", base_chunk.rfind("<table", 0, pt)) + 1
    close = base_chunk.find("</table>", open_end)
    a = re.sub(r'href="[^"]*"', 'href="{H}"', img_a, count=1)
    a = re.sub(r'src="[^"]*"', f'src="{img_url}"', a, count=1)
    a = re.sub(r'alt="[^"]*"', f'alt="{alt}"', a, count=1)
    inner = (f'<tr><td align="center" style="padding: 0; Margin: 0; font-size: 0">{a}</td></tr>'
             + gap15
             + f'<tr><td align="left" esd-text="true" class="es-m-text esd-text" style="padding: 0; Margin: 0">{NAME_P}{name}</p></td></tr>'
             + gap10
             + f'<tr><td align="left" style="padding: 0; Margin: 0" class="lp-links esd-text">{btn1}&nbsp;&nbsp;&nbsp;&nbsp;{btn2}</td></tr>')
    return base_chunk[:open_end] + inner + base_chunk[close:]

def tile(region_key, side):
    base = left_raw if side == "l" else right_raw
    img_a = img_a_l if side == "l" else img_a_r
    if region_key == "ALL":
        name = "All regions"
        img_url = f"{CDN}/tile-all.jpg"
        h_img = utm(ALL_INSPECT, "all_regions", "tile_image")
        b1 = make_btn("OPEN HOMES", utm(ALL_INSPECT, "all_regions", "open_homes"))
        b2 = make_btn("BY APPOINTMENT", utm(ALL_APPT, "all_regions", "by_appointment"))
    else:
        slug = REG_SLUG[region_key]
        name = {"LNS": "Lower North Shore", "STH": "Southern Highlands", "BYB": "Byron Bay"}[region_key]
        img_url = f"{CDN}/tile-{region_key.lower() if region_key != 'STH' else 'sh'}.jpg"
        h_img = utm(OFFICE[region_key], slug, "tile_image")
        b1 = make_btn("OPEN HOMES", utm(INSPECT[region_key], slug, "open_homes"))
        b2 = make_btn("BY APPOINTMENT", utm(OFFICE[region_key], slug, "by_appointment"))
    c = tile_cell(base, img_a, img_url, name, name, b1, b2)
    return c.replace("{H}", h_img)

def tile_row(k1, k2, last=False):
    row = tile(k1, "l") + tile(k2, "r")
    # wrap in the card-row outer structure: reuse ROW's outer skeleton by swapping cells
    outer = ROW.split(SPLITTER)[0]
    # ROW = left_raw + right_raw, and tile() already returns full left/right chunks
    return last_variant(row) if last else row

lp = (paint(open0, "#ffffff") + lp_title_tr
      + tile_row("LNS", "STH")
      + tile_row("BYB", "ALL", last=True)
      + close0)

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
new_body = head_part + lp + band + LNS_SEC + SH_SEC + BYB_SEC + offm + foot

big = styles[-1] if ".es-" in styles[-1] else None
assert big and "@media" in big
styles[-1] = styles[-1].replace("@media", "@media only screen and (max-width:600px) { .ofi-heading-wrap { white-space: normal !important } }\n@media", 1)
# launchpad underlined links: give module 1072 the same mobile override the
# region modules have, or the generic mobile button rule stretches the underline
pat = re.compile(r"\.es-module-4629\s+a\.es-button\.es-button-8305\s*\{[^}]*\}")
hits = pat.findall(styles[-1])
assert hits, "scoped 8305 override not found"
styles[-1] = pat.sub(lambda mm: mm.group(0) + "\n" + re.sub(r"\.es-module-4629\s+", ".lp-links ", mm.group(0)), styles[-1])

# launchpad sub-line smaller on mobile too
styles[-1] = pat.sub(lambda mm: mm.group(0), styles[-1])  # no-op keep
MOB_SUB = ".lp-sub { font-size: 19px !important; line-height: 24px !important }"
pm = re.compile(r"(\.lp-links a\.es-button\.es-button-8305[^}]*\})")
assert pm.search(styles[-1])
styles[-1] = pm.sub(lambda mm: mm.group(1) + "\n" + MOB_SUB, styles[-1], count=1)

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
@font-face {{ font-family: 'Fakt'; font-style: normal; font-weight: 700;
  src: url('{FCDN}/Fakt%20WOFF/FaktTT-Medium.woff2') format('woff2'),
       url('{FCDN}/Fakt%20WOFF/FaktTT-Medium.woff') format('woff'); }}
</style>"""

def brandify(html):
    html = html.replace("'times new roman', times, baskerville, georgia, serif",
                        "'Rhymes Display', 'times new roman', times, baskerville, georgia, serif")
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
for must in ["Plan your Saturday", "BROWSE BY REGION", "hq.atlas.com.au/offmarket", "Open this Saturday,"]:
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
