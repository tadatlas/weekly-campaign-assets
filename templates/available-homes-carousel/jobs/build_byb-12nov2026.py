"""Build jobs/byb-12nov2026.json: Byron Bay office homes for sale on atlas.com.au, 12 Nov 2026 (story version).
Hero and second photo per home from the website listing; no boundary lines, pins or text on either."""
import json, re
R = [  # (street, suburb, beds, baths, cars, land, hero, second, render label; renders that carry their own label stay False)
 ["28 Pacific Vista Drive", "Byron Bay", 4, 3, 2, "544sqm", "https://agentboxcdn.com.au/clients-data/26319/public_html/media/lt/1/1P10532/178902398018834315-rsd.jpg", "https://agentboxcdn.com.au/clients-data/26319/public_html/media/lt/1/1P10532/178902398514333601-rsd.jpg", False],
 ["108/116-118 Jonson Street", "Byron Bay", 2, 2, 1, "", "https://agentboxcdn.com.au/clients-data/26319/public_html/media/lt/1/1P3890/178779582611673387-rsd.jpg", "https://agentboxcdn.com.au/clients-data/26319/public_html/media/lt/1/1P3890/178779582808335547-rsd.jpg", False],
 ["4/1-3 Sunrise Boulevard", "Byron Bay", 2, 1, 0, "", "https://images.sales.reapit.com.au/26319/listing/1P11360/photo/d/1793843039905329104629061.jpg?wm=0", "https://images.sales.reapit.com.au/26319/listing/1P11360/photo/d/1793843038065345887343603.jpg?wm=0", False],
 ["443 Coorabell Road", "Coorabell", 5, 3, 3, "5acre", "https://images.sales.reapit.com.au/26319/listing/1P11278/photo/d/179024174492341866.jpg?wm=0", "https://images.sales.reapit.com.au/26319/listing/1P11278/photo/d/179023198198641618.jpg?wm=0", False],
 ["9 Edward Place", "Knockrow", 8, 6, 4, "9304sqm", "https://images.sales.reapit.com.au/26319/listing/1P10786/photo/d/178278746668362163.jpg?wm=0", "https://images.sales.reapit.com.au/26319/listing/1P10786/photo/d/178278745293113420.jpg?wm=0", False],
 ["296 Tyagarah Road", "Myocum", 3, 3, 3, "7722sqm", "https://images.sales.reapit.com.au/26319/listing/1P9718/photo/d/178901845684490376.jpg?wm=0", "https://images.sales.reapit.com.au/26319/listing/1P9718/photo/d/178901810738811469.jpg?wm=0", False],
 ["684 Bangalow Road", "Talofa", 21, 20, 40, "5hectare", "https://images.sales.reapit.com.au/26319/listing/1P10717/photo/d/178480284372056285.jpg?wm=0", "https://images.sales.reapit.com.au/26319/listing/1P10717/photo/d/178480294785283332.jpg?wm=0", False],
 ["20 Pioneers Crescent", "Bangalow", 4, 2, 4, "171acre", "https://agentboxcdn.com.au/clients-data/26319/public_html/media/lt/1/1P9705/172620786026187728-rsd.jpg", "https://agentboxcdn.com.au/clients-data/26319/public_html/media/lt/1/1P9705/172620786186493322-rsd.jpg", False],
 ["7 Booyong Road", "Clunes", 4, 2, 2, "2466sqm", "https://agentboxcdn.com.au/clients-data/26319/public_html/media/lt/1/1P10429/1762990839288578031927330-rsd.jpg", "https://agentboxcdn.com.au/clients-data/26319/public_html/media/lt/1/1P10429/1762990836349942085640127-rsd.jpg", False],
 ["33-35 Main Street", "Clunes", 0, 0, 0, "3163sqm", "https://images.sales.reapit.com.au/26319/listing/1P9858/photo/d/173197072679953514.jpg?wm=0", "https://images.sales.reapit.com.au/26319/listing/1P9858/photo/d/173197070632720003.jpg?wm=0", False],
 ["769 Fernleigh Road", "Brooklet", 5, 4, 10, "160acre", "https://agentboxcdn.com.au/clients-data/26319/public_html/media/lt/1/1P10762/1771803146768822964313301-rsd.jpg", "https://agentboxcdn.com.au/clients-data/26319/public_html/media/lt/1/1P10762/1771803146535435474551406-rsd.jpg", False],
 ["510 Wilsons Creek Road", "Wilsons Creek", 9, 13, 10, "24595sqm", "https://images.sales.reapit.com.au/26319/listing/1P10526/photo/d/179271381356137717.jpg?wm=0", "https://images.sales.reapit.com.au/26319/listing/1P10526/photo/d/179271381371701362.jpg?wm=0", False],
 ["34a Deloraine Road", "Lismore Heights", 4, 2, 2, "542sqm", "https://images.sales.reapit.com.au/26319/listing/1P10980/photo/d/178097610889922861.jpg?wm=0", "https://images.sales.reapit.com.au/26319/listing/1P10980/photo/d/1780983623642650519672535.jpg?wm=0", False],
 ["57 Kudgeree Avenue", "Cudgera Creek", 0, 0, 0, "26587sqm", "https://images.sales.reapit.com.au/26319/listing/1P11250/photo/d/178902462905522360.jpg?wm=0", "https://images.sales.reapit.com.au/26319/listing/1P11250/photo/d/1789344935031242477062917.jpg?wm=0", False],
]
# One list after the cover: Byron Bay first, then the rest of the region. The cover names the region, so no suburb intros.
def plural(n, w): return f"{n} {w}{'' if n == 1 else 'S'}"
def land(s):
    m = re.match(r"([\d.]+)(sqm|acre|hectare)", s or "")
    if not m: return ""
    n, u = m.groups(); n = int(float(n))
    return f"{n} SQM" if u == "sqm" else plural(n, u.upper())
def features(r):
    parts = [plural(n, w) for n, w in ((r[2], "BED"), (r[3], "BATH"), (r[4], "CAR")) if n]
    return "   ".join(parts) if parts else land(r[5])
def key(h): return re.sub(r"^[\dA-Za-z/\-]*\d[\dA-Za-z/\-]*\s+", "", h["street"])
hs = sorted([{"street": r[0], "suburb": r[1], "features": features(r), "photo": r[6], "photo2_story": r[7], "render": r[8]} for r in R],
            key=lambda h: (h["suburb"] != "Byron Bay", key(h)))
cards = [{"name": "Byron Bay & Northern Rivers", "intro": None, "homes": hs}]
assert sum(len(c["homes"]) for c in cards) == len(R)
job = {"name": "BYB Available Homes Carousel", "story_step": 2.0,
       "footage": "footage/byb_clips.mp4", "footage_source": "Atlas iQ Lifestyle Gallery > Byron Bay lifestyle video collection",
       "cover": {"title": "Byron Bay & Northern Rivers", "title_lines": ["Byron Bay &", "Northern Rivers"], "footage": [6.6, 9.3, 1.5], "shift": -170}, "cards": cards}
json.dump(job, open("/home/claude/weekly-campaign-assets/templates/available-homes-carousel/jobs/byb-12nov2026.json", "w"), indent=1)
for c in cards: print(c["name"], [h["street"] for h in c["homes"]])
