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

# ---- one line per copy line: card copy is shortened to fit a 360px phone ----
# Advance widths (em) of Rhymes Display Light and Fakt Normal, read from the font files.
FONT_W = {"rhymes":{"a":0.473,"b":0.513,"c":0.46,"d":0.531,"e":0.447,"f":0.286,"g":0.465,"h":0.548,"i":0.262,"j":0.24,"k":0.495,"l":0.255,"m":0.817,"n":0.555,"o":0.538,"p":0.533,"q":0.519,"r":0.372,"s":0.39,"t":0.318,"u":0.545,"v":0.462,"w":0.693,"x":0.455,"y":0.447,"z":0.436,"A":0.679,"B":0.63,"C":0.72,"D":0.776,"E":0.65,"F":0.613,"G":0.78,"H":0.784,"I":0.324,"J":0.401,"K":0.717,"L":0.622,"M":0.939,"N":0.79,"O":0.767,"P":0.584,"Q":0.767,"R":0.646,"S":0.557,"T":0.642,"U":0.774,"V":0.668,"W":0.908,"X":0.692,"Y":0.669,"Z":0.62,"0":0.539,"1":0.339,"2":0.473,"3":0.456,"4":0.484,"5":0.454,"6":0.492,"7":0.424,"8":0.505,"9":0.492," ":0.216,"/":0.449,"-":0.352,"\u2013":0.5,"&":0.726,"'":0.175,",":0.221,".":0.199,"(":0.297,")":0.297,"#":0.7},"fakt":{"a":0.524,"b":0.584,"c":0.516,"d":0.584,"e":0.524,"f":0.308,"g":0.584,"h":0.564,"i":0.24,"j":0.24,"k":0.504,"l":0.24,"m":0.864,"n":0.564,"o":0.56,"p":0.584,"q":0.58,"r":0.36,"s":0.484,"t":0.328,"u":0.56,"v":0.468,"w":0.724,"x":0.464,"y":0.468,"z":0.444,"A":0.644,"B":0.664,"C":0.712,"D":0.704,"E":0.612,"F":0.576,"G":0.76,"H":0.728,"I":0.268,"J":0.512,"K":0.652,"L":0.544,"M":0.904,"N":0.736,"O":0.76,"P":0.636,"Q":0.764,"R":0.652,"S":0.648,"T":0.588,"U":0.696,"V":0.62,"W":0.936,"X":0.596,"Y":0.608,"Z":0.584,"0":0.568,"1":0.568,"2":0.568,"3":0.568,"4":0.568,"5":0.568,"6":0.568,"7":0.568,"8":0.568,"9":0.568," ":0.22,"/":0.4,"-":0.396,"\u2013":0.556,"&":0.712,"'":0.216,",":0.256,".":0.256,"(":0.284,")":0.284,"#":0.616}}
MOBILE_COL = 149   # card column width on a 360px phone: (360 - 2*25 margin - 12 gap) / 2
ABBR = [("Street", "St"), ("Road", "Rd"), ("Crescent", "Cres"), ("Avenue", "Ave"), ("Parade", "Pde"),
        ("Place", "Pl"), ("Drive", "Dr"), ("Lane", "Ln"), ("Terrace", "Tce"), ("Close", "Cl"),
        ("Court", "Ct"), ("Highway", "Hwy"), ("Boulevard", "Blvd"), ("Circuit", "Cct"), ("Esplanade", "Esp")]

def text_w(txt, font, size, track=0.0):
    return sum(FONT_W[font].get(ch, 0.6) * size + track for ch in txt)

def card_copy(p):
    """the one-line versions of a card's copy"""
    street = p.get("street_short") or p["street"]
    for full, short in ABBR:
        street = re.sub(rf"\b{full}\b", short, street)
    suburb = re.sub(r"\s+NSW$", "", p["suburb"].strip())
    time = re.sub(r"^Saturday\b", "Sat", p["time"].strip())
    return street, suburb, time

TOO_LONG = []
def check_fit(p):
    street, suburb, time = card_copy(p)
    for label, txt, w in [("street", street, text_w(street, "rhymes", 16)),
                          ("suburb", suburb, text_w(suburb, "fakt", 11, 2)),
                          ("spec", p["spec"].replace("&nbsp;", " "), text_w(p["spec"].replace("&nbsp;", " "), "fakt", 11, 2)),
                          ("time", time, text_w(time, "fakt", 12))]:
        if round(w) > MOBILE_COL:
            TOO_LONG.append(f'{p["street"]}: {label} "{txt}" is {w:.0f}px, the mobile column is {MOBILE_COL}px')

def fill(tpl, p, region):
    street, suburb, time = card_copy(p)
    href = utm(p["url"], REG_SLUG[region], p["pid"])
    return (tpl.replace("{HREF}", href).replace("{IMG}", p["img"])
               .replace("{ALT}", p["alt"].replace('"', ""))
               # the street links to the listing: Gmail never auto-links text already inside a link, so it can't
               # fold the street + suburb + specs into one "address" link (which hid the copy on Gmail mobile)
               .replace("{STREET}", f'<a href="{href}" target="_blank" class="ofi-street" style="color: #1e1e1e; text-decoration: none">{street}</a>')
               .replace("{SUBURB}", suburb)
               .replace("{SPEC}", p["spec"])
               .replace("{TIME}", f'<span class="dtl">{time}</span>'))

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

# ---- property cards: one table per pair, one table row per element ----
# The archive's cards were two independent stacked tables, so a street name that
# wrapped to two lines pushed that card's suburb, specs and time below its
# neighbour's. Here both cards share each row (image, street, suburb, specs,
# label, time), so a taller cell makes the whole row taller and every card in a
# pair keeps the same layout in every client, Outlook included.
ROW_OPEN = LEFT_T[:LEFT_T.index("<table")]                       # <tr><td class="es-m-p25r ... es-module-8275" style="padding: 15px 30px">
assert ROW_OPEN.startswith("<tr><td") and "es-module-8275" in ROW_OPEN
ROW_CLOSE = "</td></tr>"
IMG_A = re.search(r'<a href="\{HREF\}".*?</a>', LEFT_T, re.S).group(0)
IMG_A = re.sub(r'width="263"', 'width="{W}"', IMG_A, count=1)

def _cell(label):
    """the <td ...>...</td> in LEFT_T whose text contains `label`"""
    i = LEFT_T.index(label)
    a = LEFT_T.rfind("<td", 0, i)
    return LEFT_T[a:LEFT_T.index("</td>", i) + len("</td>")]

CELLS = [_cell("{STREET}"), _cell("{SUBURB}"), _cell("{SPEC}"), _cell("OPEN INSPECTION"), _cell("{TIME}")]
GAP_AFTER = [5, 15, 15, 0, 0]        # spacing below each text row, as in the archive card

def _text_td(cell, p, region, side):
    """re-use the archive cell's td + p styles, add width/valign for the shared row"""
    if p is None:
        return f'<td class="ofi-card ofi-card-{side}" valign="top" style="padding: 0; Margin: 0; font-size: 0; line-height: 0">&nbsp;</td>'
    c = fill(cell, p, region)
    c = c.replace("<td ", f'<td valign="top" ', 1)
    return re.sub(r'class="([^"]*)"', rf'class="\1 ofi-card ofi-card-{side}"', c, count=1)

def _gap_td():
    return '<td class="es-m-w0 es-m-p10r ofi-card-gap" style="padding: 0; Margin: 0; width: 15px; font-size: 0; line-height: 0">&nbsp;</td>'

def _spacer(h):
    return (f'<tr><td colspan="3" height="{h}" style="height: {h}px; padding: 0; Margin: 0; font-size: 0; line-height: 0">&nbsp;</td></tr>')

def card_pair(pl, pr, region):
    def img(p, w, side):
        if p is None:
            return f'<td class="ofi-card ofi-card-{side}" style="padding: 0; Margin: 0; font-size: 0; line-height: 0">&nbsp;</td>'
        a = fill(IMG_A.replace("{W}", str(w)), p, region)
        return (f'<td class="ofi-card ofi-card-{side}" width="{w}" valign="top" align="left" '
                f'style="width: {w}px; padding: 0; Margin: 0; font-size: 0; line-height: 0">{a}</td>')
    rows = ['<tr>' + img(pl, 263, "l") + _gap_td() + img(pr, 262, "r") + '</tr>', _spacer(15)]
    for cell, gap in zip(CELLS, GAP_AFTER):
        rows.append('<tr>' + _text_td(cell, pl, region, "l") + _gap_td() + _text_td(cell, pr, region, "r") + '</tr>')
        if gap:
            rows.append(_spacer(gap))
    table = ('<table role="presentation" cellpadding="0" cellspacing="0" border="0" class="ofi-pair" width="540" '
             'style="width: 540px; border-collapse: collapse; border-spacing: 0px; mso-table-lspace: 0pt; mso-table-rspace: 0pt">'
             + "".join(rows) + '</table>')
    return ROW_OPEN + table + ROW_CLOSE

def build_rows(props, region):
    for p in props:
        check_fit(p)
    rows = []
    for i in range(0, len(props), 2):
        rows.append(card_pair(props[i], props[i + 1] if i + 1 < len(props) else None, region))
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

lns_head2 = paint(lns_head2, "#ffffff")   # rhythm under the top section: white, sand, white
sh_head2 = paint(sh_head2, LIGHT_SAND)
byb_head2 = paint(byb_head2, "#ffffff")

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
HEADER_BG = INK          # same near-black as the footer
ALL_BG = LIGHT_SAND      # the one sand used for every sand surface
# Rhymes Light is registered at weight 400, Fakt Normal at 400 and Fakt Medium at 500
# (see FONT_CSS). Every stack falls back to Times / Helvetica.
RHYMES = "'Rhymes Display', 'times new roman', times, baskerville, georgia, serif"
FAKT = "Fakt, helvetica, 'helvetica neue', arial, verdana, sans-serif"
LOGO = ("https://eupsscf.stripocdn.email/content/guids/CABINET_399e3ce7c0233178f8ffdcf5f73b4ebe7cc6aec5daeb767c90c6e81e04368330"
        "/images/atlas_logo_combined2.png")
NT = 'role="presentation" cellpadding="0" cellspacing="0" border="0" class="es-table-not-adapt"'
NTW = 'role="presentation" cellpadding="0" cellspacing="0" border="0"'  # full-width: Stripo keeps these at 100%
TBL = "border-collapse: collapse; border-spacing: 0px; mso-table-lspace: 0pt; mso-table-rspace: 0pt"

def fakt_p(text, cls, size=11, color=INK, weight=400, track="2px", lh="16px", align="left"):
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
    return (f'<td class="lp2-u" style="padding: 0 0 5px; Margin: 0; border-bottom: 0.5px solid {INK}; white-space: nowrap">'
            f'<a href="{href}" target="_blank" class="lp2-link" style="mso-line-height-rule: exactly; display: inline-block; '
            f'font-family: {FAKT}; font-size: 11px; line-height: 13px; letter-spacing: 2px; font-weight: 400; '
            f'text-transform: uppercase; text-decoration: none; color: {INK}; white-space: nowrap">{text}</a></td>')

def link_pair(h1, h2):
    return (f'<table {NT.replace("es-table-not-adapt", "es-table-not-adapt lp2-pair")} style="{TBL}"><tr>{ulink("OPEN HOMES", h1)}'
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
    + fakt_p("OPEN HOMES", "lp2-hdr-t", color="#ffffff", align="right")
    + fakt_p(f'<span class="dtl">{SAT_LABEL}</span>', "lp2-hdr-t", color="#ffffff", align="right")
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
        + rhymes_p(REGION_NAME[key], "lp2-name", 22)
        + f'<table {NT} style="{TBL}"><tr><td class="lp2-ngap" height="10" style="height: 10px; padding: 0; Margin: 0; font-size: 0; line-height: 0">&nbsp;</td></tr></table>'
        + link_pair(utm(INSPECT[key], slug, "open_homes"), utm(OFFICE[key], slug, "by_appointment"))
        + '</td></tr></table></td></tr>')

LIST_TR = (
    f'<tr><td align="left" class="lp2-pad" style="padding: 40px 30px 20px; Margin: 0">'
    + fakt_p("OPEN INSPECTIONS BY REGION", "lp2-eyebrow")
    + f'<table {NT} style="{TBL}"><tr><td height="12" style="height: 12px; padding: 0; Margin: 0; font-size: 0; line-height: 0">&nbsp;</td></tr></table>'
    + rhymes_p("Plan your Saturday", "lp2-title", 36, "-0.7px")
    + f'<table {NTW} width="100%" style="{TBL}; width: 100%; Margin-top: 20px">'
    + region_row("LNS") + region_row("STH") + region_row("BYB")
    + '</table></td></tr>')

ALL_TR = (
    f'<tr><td align="left" bgcolor="{ALL_BG}" class="lp2-all" style="background-color: {ALL_BG}; padding: 10px 30px; Margin: 0">'
    f'<table {NT.replace("es-table-not-adapt", "es-table-not-adapt lp2-all-in")} style="{TBL}; Margin: 0"><tr>'
    f'<td class="lp2-all-lbl" width="144" height="36" align="left" valign="middle" style="width: 144px; height: 36px; padding: 0 0 6px; Margin: 0; white-space: nowrap">'
    + fakt_p("ALL", "lp2-all-t")
    + f'</td><td class="lp2-gap lp2-all-gap" width="24" style="width: 24px; padding: 0; Margin: 0; font-size: 0; line-height: 0">&nbsp;</td>'
    f'<td valign="middle" class="lp2-all-links" style="padding: 0; Margin: 0">'
    + link_pair(utm(ALL_INSPECT, "all_regions", "open_homes"), utm(ALL_APPT, "all_regions", "by_appointment"))
    + '</td></tr></table></td></tr>')

lp = paint(open0, "#ffffff") + LIST_TR + ALL_TR + close0

# Mobile sizes from the 375px frame (37:3). Selectors are scoped to beat Stripo's
# generic ".es-content-body p / a { font-size: 14px !important }" and "p, a { line-height: 150% }".
LP2_MOBILE = """@media only screen and (max-width:600px) {
 .es-header-body td.lp2-hdr { padding: 23px 25px !important }
 .es-header-body p.lp2-hdr-t { font-size: 11px !important; line-height: 16px !important }
 .es-content-body td.lp2-pad { padding: 32px 25px 24px !important }
 .es-content-body p.lp2-title { font-size: 32px !important; line-height: 37px !important }
 .es-content-body p.lp2-eyebrow { font-size: 11px !important; line-height: 16px !important }
 .es-content-body td.lp2-row { padding: 12px 0 !important }
 .es-content-body td.lp2-thumb { width: 80px !important }
 .es-content-body img.lp2-img { width: 80px !important; height: 40px !important }
 .es-content-body td.lp2-gap { width: 14px !important }
 .es-content-body p.lp2-name { font-size: 18px !important; line-height: 22px !important }
 .es-content-body td.lp2-ngap { height: 2px !important }
 .es-content-body a.lp2-link { font-size: 11px !important; line-height: 13px !important }
 .es-content-body table.lp2-pair { width: 100% !important }
 .es-content-body table.lp2-pair td.lp2-u { display: inline-block !important; vertical-align: top; Margin: 4px 0 !important }
 .es-content-body table.lp2-pair td.lp2-lgap { display: inline-block !important; width: 14px !important }
 .es-content-body td.lp2-all { padding: 10px 25px !important }
 .es-content-body td.lp2-all-lbl { width: 80px !important; height: 36px !important }  /* = thumbnail column, so the links line up */
 .es-content-body p.lp2-all-t { font-size: 11px !important; line-height: 16px !important; text-align: left !important; white-space: nowrap !important }
 .es-content-body td.lp2-all-gap { width: 14px !important }
 .es-content-body td.lp2-all-links table.lp2-pair td.lp2-u { Margin: 0 !important }
 .es-content-body td.ofi-card { width: 50% !important }
 /* the gap lives in the card padding: a separate gap cell gets squeezed to 0 between two 50% columns */
 .es-content-body td.ofi-card-l { padding: 0 6px 0 0 !important }
 .es-content-body td.ofi-card-r { padding: 0 0 0 6px !important }
 .es-content-body td.ofi-card-gap { display: none !important }
 .es-content-body table.ofi-pair { table-layout: fixed !important }
 .es-content-body td.ofi-card p { white-space: nowrap !important; overflow: hidden !important; text-overflow: ellipsis !important }
 .es-content-body td.ofi-card p a.ofi-street { font-size: inherit !important; line-height: inherit !important; color: #1e1e1e !important; text-decoration: none !important }
}
@media only screen and (max-width:374px) {
 .es-content-body td.lp2-thumb, .es-content-body td.lp2-row td.lp2-gap { display: none !important }
 .es-content-body td.lp2-all-lbl { width: auto !important }
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
# ActiveCampaign adds its own unsubscribe link, so drop the archive's plain-text UNSUBSCRIBE row
ui = foot.find(">UNSUBSCRIBE</p>")
assert ui > 0, "footer UNSUBSCRIBE row not found"
u_tr = foot.rfind("<tr>", 0, ui)
foot = foot[:u_tr] + foot[tr_block(foot, u_tr):]
assert "UNSUBSCRIBE" not in foot.upper().replace("UNSUBSCRIBE/2", "")
# PRIVACY POLICY was plain text: link it to the site's policy page
PRIVACY = "https://www.atlas.com.au/privacy-policy"
pp = re.search(r'(<p [^>]*color: #5e5e5e[^>]*>)PRIVACY POLICY</p>', foot)
assert pp, "footer PRIVACY POLICY not found"
foot = foot.replace(pp.group(0), pp.group(1) + f'<a href="{PRIVACY}" target="_blank" style="color: #5e5e5e; text-decoration: none">PRIVACY POLICY</a></p>', 1)

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

# ---------- type system: one caps style and one ink across the email ----------
# Caps labels and links are Fakt Normal 11px / 2px tracking on desktop AND mobile.
# Stripo dropped some of them to 10px on mobile; the off-market button was 10px / 1.5px.
new_body, n = re.subn(r'(<p class="[^"]*)es-text-mobile-size-10([^"]*" style="[^"]*letter-spacing: 2px[^"]*font-size: 11px)',
                      r"\1es-text-mobile-size-11\2", new_body)
new_body, n2 = re.subn(r'(<p class="[^"]*)es-text-mobile-size-10([^"]*" style="[^"]*font-size: 11px[^"]*letter-spacing: 2px)',
                       r"\1es-text-mobile-size-11\2", new_body)
assert n + n2 >= 38, ("caps labels not re-sized on mobile", n, n2)
m = re.search(r'<a [^>]*class="es-button es-button-7720"[^>]*>', new_body)
assert m, "off-market button not found"
reg = m.group(0).replace("letter-spacing: 1.5px", "letter-spacing: 2px")
reg = re.sub(r"font-size: ?10px", "font-size: 11px", reg)
new_body = new_body.replace(m.group(0), reg)
for i, st in enumerate(styles):
    st = re.sub(r"(a\.es-button\.es-button-(?:7720|2326|3667|8305)\s*\{\s*font-size:\s*)10px", r"\g<1>11px", st)
    styles[i] = st
# every link underline is a 0.5px rule (VIEW REGION's button border was 1px)
new_body, nu = re.subn(r"border-width: ?0px 0px 1px 0px", "border-width: 0px 0px 0.5px 0px", new_body)
assert nu == 3, ("expected 3 VIEW REGION underlines", nu)
# property card text was #333333 / #292929 beside #1e1e1e names; use the one ink
new_body = re.sub(r"color: ?#(?:333333|292929)\b", "color: #1e1e1e", new_body, flags=re.I)

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

# ---------- Gmail-safe CSS ----------
# The Gmail apps drop a whole <style> block when it is over ~16 KB or contains a
# selector they don't support (attribute selectors like a[x-apple-data-detectors],
# ids, the * wildcard). Stripo's CSS was one 43 KB block, so on Gmail mobile every
# mobile rule was lost and the desktop layout showed, shrunk. Here the CSS is
# de-duplicated, stripped of unsupported selectors, and split into blocks under
# 15 KB. Rules Gmail can't read (Apple/Samsung fixes) go in a block of their own,
# so Gmail can drop that block without losing the rest.
GMAIL_BLOCK = 15000

def _statements(css):
    """split CSS into top-level statements: ('rule', sel, body) or ('at', prelude, inner)"""
    out, i, n = [], 0, len(css)
    while i < n:
        j = css.find("{", i)
        if j < 0:
            break
        prelude = css[i:j].strip()
        depth, k = 1, j + 1
        while depth and k < n:
            depth += {"{": 1, "}": -1}.get(css[k], 0)
            k += 1
        inner = css[j + 1:k - 1]
        out.append(("at", prelude, inner) if prelude.startswith("@") else ("rule", prelude, inner))
        i = k
    return out

def _gmail_ok(sel):
    return not re.search(r"\[|#|(^|\s)\*(\s|$)|\s\*$", sel)

def _min(x):
    return re.sub(r"\s*([{};:,])\s*", r"\1", re.sub(r"\s+", " ", x)).strip()

def gmail_safe_style_blocks(css_list):
    css = "\n".join(re.sub(r"/\*.*?\*/", "", c, flags=re.S) for c in css_list)
    safe, other, seen = [], [], set()
    def take(sel, body, media=None):
        sels = [x.strip() for x in sel.split(",") if x.strip()]
        # "X *" (everything inside X) isn't supported by Gmail: name the children it covers instead
        sels = [y for x in sels for y in ([x[:-1].rstrip() + " " + t for t in ("a", "span", "strong")]
                                          if re.fullmatch(r".+\s\*", x) else [x])]
        ok = [x for x in sels if _gmail_ok(x)]
        bad = [x for x in sels if not _gmail_ok(x) and not re.fullmatch(r".*\s\*", x) and x != "*"]
        body = _min(body)
        for group, dest in ((ok, safe), (bad, other)):
            if group:
                key = (media, ",".join(group), body)
                if key not in seen:
                    seen.add(key); dest.append((media, ",".join(group) + "{" + body + "}"))
    for kind, pre, inner in _statements(css):
        if kind == "rule":
            take(pre, inner)
        elif pre.startswith("@media"):
            for k2, p2, i2 in _statements(inner):
                if k2 == "rule":
                    take(p2, i2, _min(pre))
        else:                       # @font-face etc. stay as they are
            other.append((None, _min(pre) + "{" + _min(inner) + "}"))
    def pack(items):
        blocks, cur, cur_media, size = [], [], None, 0
        def flush():
            nonlocal cur, cur_media, size
            if cur:
                txt = "".join(cur)
                blocks.append(txt if cur_media is None else cur_media + "{" + txt + "}")
            cur, size = [], 0
        for media, rule in items:
            extra = len(rule) + (len(media) + 2 if media and media != cur_media else 0)
            if media != cur_media or size + extra > GMAIL_BLOCK - 200:
                # group consecutive rules of the same media query; start a new chunk when full
                if media != cur_media or size + extra > GMAIL_BLOCK - 200:
                    flush()
                cur_media = media
            cur.append(rule); size += len(rule)
        flush()
        # merge small neighbouring chunks into blocks under the limit
        merged, buf = [], ""
        for b in blocks:
            if len((buf + b).encode()) > GMAIL_BLOCK:
                merged.append(buf); buf = ""
            buf += b
        if buf:
            merged.append(buf)
        return merged
    out = [f'<style type="text/css">{b}</style>' for b in pack(safe)]
    out += [f'<style type="text/css">{b}</style>' for b in pack(other)]
    for b in out:
        assert len(b.encode()) <= GMAIL_BLOCK + 100, len(b.encode())
    return out

# footer logo had an empty alt
new_body, na = re.subn(r'(<img\b[^>]*?)alt=""([^>]*atlas_logo_combined2\.png)', r'\1alt="Atlas"\2', new_body)
new_body, nb = re.subn(r'(<img\b[^>]*atlas_logo_combined2\.png"[^>]*?)alt=""', r'\1alt="Atlas"', new_body)
assert 'alt=""' not in new_body, "image without alt text"

STYLE_BLOCKS = "\n".join(gmail_safe_style_blocks([re.sub(r"</?style[^>]*>", "", x) for x in styles]))
# inline CSS variables (Stripo dark-mode layer) can make Gmail discard the style attribute
new_body = re.sub(r"background-image:\s*none,\s*var\(--[^)]*\);?\s*", "", new_body)
assert "var(--" not in new_body

doc = f"""<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width, initial-scale=1" />
<meta http-equiv="X-UA-Compatible" content="IE=edge" />
<meta name="x-apple-disable-message-reformatting" />
<title>{TITLE_DATE} Weekly OFI Email</title>
{FONT_CSS}
{STYLE_BLOCKS}
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
for must in ["Plan your Saturday", "OPEN INSPECTIONS BY REGION", ">ALL</p>", "hq.atlas.com.au/offmarket",
             f"SATURDAY {SAT.day} {SAT.strftime('%B').upper()}", "thumb-lns.jpg", "thumb-sh.jpg", "thumb-byb.jpg"]:
    assert must in doc, must
for k in ("LNS", "STH", "BYB"):
    for p in data[k]:
        assert card_copy(p)[0] in doc, card_copy(p)[0]
        assert not re.search(r"(^|\s)0 (BED|BATH|CAR)", p["spec"]), p["street"]
assert "OPEN TODAY" not in doc

open(OUT, "w", encoding="utf-8").write(doc)
print("written", OUT, len(doc), "bytes")
if TOO_LONG:
    print("\nWARNING: these card lines are too long for one line on a 360px phone. They will be cut with an ellipsis on")
    print("mobile. Add a shorter \"street_short\" to the dataset (e.g. drop \"Villa\" or the unit prefix):")
    for t in TOO_LONG:
        print("  -", t)
    print()
print("tables balanced:", doc.count("<table") == doc.count("</table>"), doc.count("<table"))
print("divs:", doc.count("<div"), doc.count("</div>"))

# ---------- 9. XHTML pass (Stripo importer needs strict XML) — always the last step ----------
import subprocess
subprocess.run([sys.executable, os.path.join(HERE, "qa", "xhtml_pass.py"), OUT], check=True)
