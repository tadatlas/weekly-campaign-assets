"""Build jobs/sh-12nov2026.json from the 51 STH For Sale listings (Notion property sync, 11 Nov 19:00Z)."""
import json, re
R = [  # (id, address, suburb, beds, baths, cars, land, hero)
("1P11356","820-916 Sheepwash Road Avoca NSW","Avoca",0,0,0,"161hectare","https://images.sales.reapit.com.au/26319/listing/1P11356/photo/d/179126599466921030.jpg?wm=0"),
("1P11253","1 Thompson Street Bowral NSW","Bowral",3,1,1,"974sqm","https://images.sales.reapit.com.au/26319/listing/1P11253/photo/d/179203439932904544.jpg?wm=0"),
("1P11132","11 Bloomfield Close Bowral NSW","Bowral",5,3,2,"8002sqm","https://images.sales.reapit.com.au/26319/listing/1P11132/photo/d/178398984778307737.jpg"),
("1P10300","11 Lavis Road Bowral NSW","Bowral",4,2,2,"1037sqm","https://images.sales.reapit.com.au/26319/listing/1P10300/photo/d/178938006417137755.jpg?wm=0"),
("1P10756","112-116 Shepherd Street Bowral NSW","Bowral",3,3,3,"2787sqm","https://images.sales.reapit.com.au/26319/listing/1P10756/photo/d/177380883588765964.jpg?wm=0"),
("1P11241","127 Bowral Street Bowral NSW","Bowral",4,2,2,"797sqm","https://images.sales.reapit.com.au/26319/listing/1P11241/photo/d/178901923559341011.jpg?wm=0"),
("1P11326","14A Cypress Parade Bowral NSW","Bowral",3,3,2,"1170sqm","https://images.sales.reapit.com.au/26319/listing/1P11326/photo/d/179090475783133841.jpg?wm=0"),
("1P10828","16 Gibraltar Road Bowral NSW","Bowral",4,3,6,"6acre","https://images.sales.reapit.com.au/26319/listing/1P10828/photo/d/178330217295919559.jpg?wm=0"),
("1P11208","17 Gibraltar Road Bowral NSW","Bowral",4,2,2,"1hectare","https://images.sales.reapit.com.au/26319/listing/1P11208/photo/d/179023234779953514.jpg?wm=0"),
("1P11044","19 Elm Street Bowral NSW","Bowral",4,2,1,"924sqm","https://images.sales.reapit.com.au/26319/listing/1P11044/photo/d/178702548747750802.jpg?wm=0"),
("1P11172","21 Glenquarry Crescent Bowral NSW","Bowral",5,2,3,"901sqm","https://images.sales.reapit.com.au/26319/listing/1P11172/photo/d/179263817552254860.jpg?wm=0"),
("1P11154","22 Kimberley Drive Bowral NSW","Bowral",5,4,4,"2hectare","https://images.sales.reapit.com.au/26319/listing/1P11154/photo/d/178494304849858444.jpg?wm=0"),
("1P10917","25 Rosemary Crescent Bowral NSW","Bowral",6,3,2,"1924sqm","https://images.sales.reapit.com.au/26319/listing/1P10917/photo/d/178772291139998216.jpg?wm=0"),
("1P11199","3 Centennial Road Bowral NSW","Bowral",4,2,2,"4032sqm","https://images.sales.reapit.com.au/26319/listing/1P11199/photo/d/179296678071809607.jpg?wm=0"),
("1P11150","3 Westbrook Crescent Bowral NSW","Bowral",4,2,2,"800sqm","https://images.sales.reapit.com.au/26319/listing/1P11150/photo/d/179031036433670591.jpg?wm=0"),
("1P11406","31/9 Kangaloon Road Bowral NSW","Bowral",3,2,2,None,"https://images.sales.reapit.com.au/26319/listing/1P11406/photo/d/179358600406814823.jpg?wm=0"),
("1P11055","34 Victoria Street Bowral NSW","Bowral",4,3,2,"2155sqm","https://images.sales.reapit.com.au/26319/listing/1P11055/photo/d/178951578066831096.jpg?wm=0"),
("1P10964","4/65-67 Kangaloon Road Bowral NSW","Bowral",3,2,2,"355sqm","https://images.sales.reapit.com.au/26319/listing/1P10964/photo/d/177694238715942903.jpg?wm=0"),
("1P11311","42-44 Old South Road Bowral NSW","Bowral",4,2,3,"1851sqm","https://images.sales.reapit.com.au/26319/listing/1P11311/photo/d/179074396152424346.jpg?wm=0"),
("1P10713","50 Park Road Bowral NSW","Bowral",4,2,1,"796sqm","https://images.sales.reapit.com.au/26319/listing/1P10713/photo/d/178789049372219320.jpg?wm=0"),
("1P11303","6/18 Kangaloon Road Bowral NSW","Bowral",3,2,2,"325sqm","https://images.sales.reapit.com.au/26319/listing/1P11303/photo/d/179187218252908405.jpg?wm=0"),
("1P11201","8 College Place Bowral NSW","Bowral",4,2,1,"903sqm","https://images.sales.reapit.com.au/26319/listing/1P11201/photo/d/178944362064967755.jpg?wm=0"),
("1P11374","91B Shepherd Street Bowral NSW","Bowral",4,3,2,"4175sqm","https://images.sales.reapit.com.au/26319/listing/1P11374/photo/d/179375553555770084.jpg?wm=0"),
("1P11136",None,"Bowral",0,0,0,"100acre","https://images.sales.reapit.com.au/26319/listing/1P11136/photo/d/179255249289802636.jpg?wm=0"),
("1P11380","Villa 71/2-18 Centennial Road Bowral NSW","Bowral",2,2,2,None,"https://images.sales.reapit.com.au/26319/listing/1P11380/photo/d/179315304932161782.jpg?wm=0"),
("1P11392","31 Grice Drive Bundanoon NSW","Bundanoon",5,2,2,"2000sqm","https://images.sales.reapit.com.au/26319/listing/1P11392/photo/d/179332198803709537.jpg?wm=0"),
("1P11210","63 Hazelton Road Bungonia NSW","Bungonia",3,2,4,"112acre","https://images.sales.reapit.com.au/26319/listing/1P11210/photo/d/178962448096842339.jpg?wm=0"),
("1P11161","1A Burradoo Road Burradoo NSW","Burradoo",4,2,2,"1800sqm","https://images.sales.reapit.com.au/26319/listing/1P11161/photo/d/178899982162796251.jpg?wm=0"),
("1P11214","5A Eridge Park Road Burradoo NSW","Burradoo",6,3,3,"4000sqm","https://images.sales.reapit.com.au/26319/listing/1P11214/photo/d/178648881000777492.jpg?wm=0"),
("1P11351",None,"Burradoo",5,5,4,"5038sqm","https://images.sales.reapit.com.au/26319/listing/1P11351/photo/d/179193839130345973.jpg?wm=0"),
("1P11148","15 Middle Road Exeter NSW","Exeter",3,2,1,"1629sqm","https://images.sales.reapit.com.au/26319/listing/1P11148/photo/d/178401206647354877.jpg?wm=0"),
("1P11219","506 Old Argyle Road Exeter NSW","Exeter",4,4,3,None,"https://agentboxcdn.com.au/clients-data/26319/public_html/media/lt/1/1P11219/178910642453628039-rsd.jpg"),
("1P11138","51 Middle Road Exeter NSW","Exeter",5,5,8,"2000sqm","https://agentboxcdn.com.au/clients-data/26319/public_html/media/lt/1/1P11138/178406851122426622-rsd.jpg"),
("1P10513",None,"Exeter",4,1,0,"90hectare","https://images.sales.reapit.com.au/26319/listing/1P10513/photo/d/176059320273671281.jpg?wm=0"),
("1P10441",None,"Exeter",8,6,5,"120hectare","https://agentboxcdn.com.au/clients-data/26319/public_html/media/lt/1/1P10441/176066168100861621-rsd.jpg"),
("1P11204","103 Redhills Road Fitzroy Falls NSW","Fitzroy Falls",5,5,6,"40hectare","https://agentboxcdn.com.au/clients-data/26319/public_html/media/lt/1/1P11204/178839459791172359-rsd.jpg"),
("1P11205",None,"Fitzroy Falls",3,2,2,"76acre","https://images.sales.reapit.com.au/26319/listing/1P11205/photo/d/178830925240094255.jpg?wm=0"),
("1P11153","164 Princes Highway Kiama Heights NSW","Kiama Heights",2,1,0,"45hectare","https://images.sales.reapit.com.au/26319/listing/1P11153/photo/d/178720494050309685.jpg?wm=0"),
("1P10875","136 Old Hume Highway Mittagong NSW","Mittagong",4,2,1,"392sqm","https://images.sales.reapit.com.au/26319/listing/1P10875/photo/d/178469405448156066.jpg?wm=0"),
("1P11147","10 Dormie Place Moss Vale NSW","Moss Vale",0,0,0,None,"https://images.sales.reapit.com.au/26319/listing/1P11147/photo/d/178426252078146482.jpg?wm=0"),
("1P11340","14 Meehan Place Moss Vale NSW","Moss Vale",0,0,0,"2095sqm","https://images.sales.reapit.com.au/26319/listing/1P11340/photo/d/179184426589993068.jpg?wm=0"),
("1P11290","19 Eliza Street Moss Vale NSW","Moss Vale",4,2,2,"690sqm","https://images.sales.reapit.com.au/26319/listing/1P11290/photo/d/179012125056476297.jpg?wm=0"),
("1P11110","259 Headlam Road Moss Vale NSW","Moss Vale",4,2,6,"2hectare","https://agentboxcdn.com.au/clients-data/26319/public_html/media/lt/1/1P11110/178364027649156792-rsd.jpg"),
("1P11142","30 Watson Road Moss Vale NSW","Moss Vale",4,2,2,"2022sqm","https://images.sales.reapit.com.au/26319/listing/1P11142/photo/d/178407954604137125.jpg?wm=0"),
("1P10579","31 Rosella Avenue Moss Vale NSW","Moss Vale",4,2,2,"610sqm","https://images.sales.reapit.com.au/26319/listing/1P10579/photo/d/179081560737752680.jpg?wm=0"),
("1P11020","33 Browley Street Moss Vale NSW","Moss Vale",2,1,1,"631sqm","https://agentboxcdn.com.au/clients-data/26319/public_html/media/lt/1/1P11020/177793645241678044-rsd.jpg"),
("1P11169","46 Darraby Drive Moss Vale NSW","Moss Vale",5,3,2,"695sqm","https://images.sales.reapit.com.au/26319/listing/1P11169/photo/d/178426428614943821.jpg?wm=0"),
("1P10714","28 Windeyer Street Renwick NSW","Renwick",4,2,2,"606sqm","https://agentboxcdn.com.au/clients-data/26319/public_html/media/lt/1/1P10714/178833176841335493-rsd.jpg"),
("1P10716","34 Windeyer Street Renwick NSW","Renwick",4,2,4,"635sqm","https://images.sales.reapit.com.au/26319/listing/1P10716/photo/d/178833203741335493.jpg?wm=0"),
("1P10576","312 Oldbury Road Sutton Forest NSW","Sutton Forest",5,4,5,"16hectare","https://agentboxcdn.com.au/clients-data/26319/public_html/media/lt/1/1P10576/176483105887212223-rsd.jpg"),
("1P11018",None,"Wingello",0,0,0,"165acre","https://images.sales.reapit.com.au/26319/listing/1P11018/photo/d/178718837196754834.jpg?wm=0"),
]
# Address withheld on the website: the estate name from the listing headline where it has one, otherwise "Address on request".
WITHHELD = {"1P11351": "Amanzi", "1P10441": "Virginia Park", "1P11018": "Benbullen"}
AOR = "Address on request"

# Hero photos with baked-in graphics (boundary lines, labels, map pin) or just a sign: use the listing's second photo.
SECOND = {
 "1P11136": "https://images.sales.reapit.com.au/26319/listing/1P11136/photo/d/179135009756739119.jpg?wm=0",
 "1P11340": "https://images.sales.reapit.com.au/26319/listing/1P11340/photo/d/179184426605461736.jpg?wm=0",
 "1P10513": "https://images.sales.reapit.com.au/26319/listing/1P10513/photo/d/176059311898932124.jpg?wm=0",
 "1P11205": "https://images.sales.reapit.com.au/26319/listing/1P11205/photo/d/178702634239116207.jpg?wm=0",
 "1P11356": "https://images.sales.reapit.com.au/26319/listing/1P11356/photo/d/179126601467862315.jpg?wm=0",
}
# Too long for one line of the Rhymes title: "Villa 71/2-18" is the same address as "71/2-18".
SHORT = {"1P11380": "71/2-18 Centennial Road"}

def street(r):
    if r[0] in SHORT: return SHORT[r[0]]
    if r[1] is None: return WITHHELD.get(r[0], AOR)
    return re.sub(r"\s+" + re.escape(r[2]) + r"\s+NSW$", "", r[1])
def plural(n, w): return f"{n} {w}{'' if n == 1 else 'S'}"
def land(s):
    m = re.match(r"([\d.]+)(sqm|acre|hectare)", s or "")
    if not m: return ""
    n, u = m.groups(); n = int(float(n))
    return f"{n} SQM" if u == "sqm" else plural(n, u.upper())
def features(r):
    parts = [plural(n, w) for n, w in ((r[3], "BED"), (r[4], "BATH"), (r[5], "CAR")) if n]
    return "   ".join(parts) if parts else land(r[6])
def key(h):  # A to Z by street name without the number; named and withheld listings after the streets
    s = h["street"]
    if not re.search(r"\d", s): return (1, s == AOR, s)
    return (0, re.sub(r"^(Villa\s+)?[\dA-Za-z/\-]*\d[\dA-Za-z/\-]*\s+", "", s), s)

homes = {}
for r in R:
    homes.setdefault(r[2], []).append({"street": street(r), "suburb": r[2], "features": features(r), "photo": SECOND.get(r[0], r[7]), "render": False, "id": r[0]})
F = "footage/sh/"
GROUPS = [  # (card name, suburbs, intro shots per suburb in display order, title_lines)
    ("Bowral", ["Bowral"], {"Bowral": [F + "bowral_aerial.jpg", 0.5]}, None),
    ("Burradoo", ["Burradoo"], {"Burradoo": [F + "autumn_drive.jpg", 0.5]}, None),
    ("Moss Vale", ["Moss Vale"], {"Moss Vale": [F + "cattle.jpg", 0.5]}, None),
    ("Mittagong, Renwick", ["Mittagong", "Renwick"], {"Renwick": [F + "tall_trees.jpg", 0.5], "Mittagong": [F + "golden_hills.jpg", 0.5]}, None),
    ("Exeter, Sutton Forest, Wingello, Bundanoon", ["Exeter", "Sutton Forest", "Wingello", "Bundanoon"],
     {"Exeter": [F + "sheep_gate.jpg", 0.5], "Sutton Forest": [F + "rolling_green.jpg", 0.5], "Wingello": [F + "misty_pasture.jpg", 0.5], "Bundanoon": [F + "forest_walk.jpg", 0.5]}, None),
    ("Fitzroy Falls, Avoca", ["Fitzroy Falls", "Avoca"], {"Avoca": [F + "valley_mist.jpg", 0.5], "Fitzroy Falls": [F + "fitzroy_falls.jpg", 0.3]}, None),
    ("Southern Tablelands & South Coast", ["Bungonia", "Kiama Heights"], {"x": [F + "pastel_sunset.jpg", 0.5]}, ["Southern Tablelands &", "South Coast"]),
]
cards = []
for name, subs, shots, lines in GROUPS:
    hs = sorted([h for s in subs for h in homes.pop(s)], key=key)
    intro = {"title_lines": lines, "shots": [list(v) for v in shots.values()]} if lines else None
    if not lines:  # suburbs in display order: the first home's suburb last
        order = [s for s in shots if s != hs[0]["suburb"]] + [hs[0]["suburb"]]
        intro = {"titles": order, "shots": [shots[s] for s in order]}
    cards.append({"name": name, "intro": intro, "homes": hs})
assert not homes, homes
job = {"name": "SH Available Homes Carousel",
       "cover": {"title": "Southern Highlands", "image": F + "ranges_sunset.jpg", "x": 0.2, "duration": 5.0},
       "cards": cards}
print(sum(len(c["homes"]) for c in cards), "homes")
for c in cards:
    print(f'{c["name"]:45s} {len(c["homes"]):3d}  intro: {c["intro"].get("titles") or c["intro"]["title_lines"]}')
json.dump(job, open("/home/claude/weekly-campaign-assets/templates/available-homes-carousel/jobs/sh-12nov2026.json", "w"), indent=1)
