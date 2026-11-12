"""Build jobs/lns-lease-12nov2026.json: Jaime Pratt's LNS rentals (Notion property sync, 11 Nov 19:00Z) plus a featured rental."""
import json, re, os
HERE = os.path.dirname(os.path.abspath(__file__))
R = [  # (id, address, suburb, beds, baths, cars, rent display, photo)
("1P10451","71/30 Moore Road Freshwater NSW","Freshwater",1,1,0,"$1,650 pw","https://images.sales.reapit.com.au/26319/listing/1P10451/photo/d/1758242529648614594144063.jpg?wm=0"),
("1P11202","17b Stanton Road Mosman NSW","Mosman",4,3,2,"$4,000 pw","https://images.sales.reapit.com.au/26319/listing/1P11202/photo/d/178547505035850672.jpg?wm=0"),
("1P11293","7 Stanton Road Mosman NSW","Mosman",5,4,3,"$4500 pw","https://images.sales.reapit.com.au/26319/cms/9/1204/d/1404461938.jpg?wm=0"),
("1P4767","83 Bay Street Mosman NSW","Mosman",6,4,4,"$2,950 per week","https://agentboxcdn.com.au/clients-data/26319/public_html/media/lt/1/1P4767/1404467195-rsd.jpg"),
("1P11417","Unit 1/12 Waitovu Street Mosman NSW","Mosman",3,2,1,"$3,400 pw","https://images.sales.reapit.com.au/26319/cms/9/555/d/1404468972.jpg?wm=0"),
("1P11412","Unit 13/68 Bradleys Head Road Mosman NSW","Mosman",1,1,0,"$925 pw","https://images.sales.reapit.com.au/26319/cms/9/1291/d/178787150448608125.jpg?wm=0"),
("1P11416","Unit 205/36 Spit Road Mosman NSW","Mosman",2,2,1,"$1,300 pw","https://images.sales.reapit.com.au/26319/cms/9/1304/d/1404461278.jpg?wm=0"),
("1P11247","Unit 301/171-179 Avenue Road Mosman NSW","Mosman",3,3,3,"$4,200 pw","https://images.sales.reapit.com.au/26319/cms/9/1020/d/177459121002030908.jpg?wm=0"),
("1P11285","Unit 5/17 Warringah Road Mosman NSW","Mosman",4,2,2,"$3,500 pw","https://images.sales.reapit.com.au/26319/cms/9/1184/d/177033228442591405.jpg?wm=0"),
("1P11393","101/96-98 Ben Boyd Road Neutral Bay NSW","Neutral Bay",3,2,2,"$3,600 pw","https://images.sales.reapit.com.au/26319/listing/1P11393/photo/d/179306550547284517.jpg?wm=0"),  # hero is virtually staged; its label would be cropped off
("1P11384","6.01/20 Premier Street Neutral Bay NSW","Neutral Bay",3,2,2,"$2,950 pw","https://images.sales.reapit.com.au/26319/cms/9/810/d/1759810848045651045775015.jpg?wm=0"),
("1P11350","1 Seaforth Crescent Seaforth NSW","Seaforth",4,5,3,"$5,500.00 pw","https://images.sales.reapit.com.au/26319/cms/9/1238/d/177251522026937769.jpg?wm=0"),
]
def street(r): return re.sub(r"^Unit\s+", "", re.sub(r"\s+" + re.escape(r[2]) + r"\s+NSW$", "", r[1]))
def rent(s):  # "$4500 pw", "$5,500.00 pw", "$2,950 per week" -> "$4,500 PW"
    n = int(float(re.sub(r"[^\d.]", "", s.split("p")[0]))); return f"${n:,} PW"
def plural(n, w): return f"{n} {w}{'' if n == 1 else 'S'}"
def features(r):
    return "   ".join([plural(n, w) for n, w in ((r[3], "BED"), (r[4], "BATH"), (r[5], "CAR")) if n] + [rent(r[6])])
def key(h): return re.sub(r"^[\dA-Za-z./\-]*\d[\dA-Za-z./\-]*\s+", "", h["street"])
homes = {}
for r in R: homes.setdefault(r[2], []).append({"street": street(r), "suburb": r[2], "features": features(r), "photo": r[7], "render": False, "id": r[0]})
# One full-bleed card per rental, A to Z by street. No list, no featured listing, no opens.
X = {   # crop position across each landscape photo (0 left, 1 right), chosen from five options per photo so the subject leads
 "1P11247": 0.4,  "1P4767": 0.4,   "1P11393": 0.0,   # Ben Boyd is virtually staged: 0.0 keeps its "Virtually staged" label in frame
 "1P11412": 0.7,  "1P10451": 0.0,  "1P11384": 0.75,
 "1P11350": 0.3,  "1P11416": 0.5,  "1P11202": 0.8,
 "1P11293": 0.2,  "1P11417": 0.6,  "1P11285": 0.65,
}
def rent_line(h): return h["features"].rsplit("   ", 1)[1].replace(" PW", " per week")
def feat_line(h): return h["features"].rsplit("   ", 1)[0]
cards = [{"name": h["street"], "still": True, "feature": {"title": h["street"], "suburb": h["suburb"],
          "lines": [feat_line(h), rent_line(h)], "shots": [[h["photo"], X.get(h["id"], 0.5)]]}}
         for h in sorted([h for hs in homes.values() for h in hs], key=key)]
job = {"name": "LNS For Lease Carousel", "caps": "For lease", "footage": "footage/lns_clips.mp4",
       "cover": {"title": "Lower North Shore", "footage": [33.6, 39.5]}, "cards": cards}
json.dump(job, open(os.path.join(HERE, "lns-lease-12nov2026.json"), "w"), indent=1)
for c in cards: print(c["name"], "|", " / ".join(c["feature"]["lines"]))
