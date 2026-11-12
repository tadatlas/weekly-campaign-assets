"""Fetch the brand fonts (Rhymes Display Light, Fakt Normal/Medium) from the
atlas-app-fonts repo and convert them to TTF in ./fonts. Run once per machine."""
import os, urllib.request
from fontTools.ttLib import TTFont
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "fonts")
BASE = "https://cdn.jsdelivr.net/gh/tadatlas/atlas-app-fonts@main/"
FILES = {
    "RhymesDisplay-Light.ttf": "rhymes%20woff/Rhymes%20Display%20Light.woff",
    "Fakt-Normal.ttf": "Fakt%20WOFF/FaktTT-Normal.woff",
    "Fakt-Medium.ttf": "Fakt%20WOFF/FaktTT-Medium.woff",
}
def ensure():
    os.makedirs(OUT, exist_ok=True)
    for name, src in FILES.items():
        dst = os.path.join(OUT, name)
        if os.path.exists(dst):
            continue
        tmp = dst + ".woff"
        urllib.request.urlretrieve(BASE + src, tmp)
        f = TTFont(tmp); f.flavor = None; f.save(dst); os.remove(tmp)
    return OUT
if __name__ == "__main__":
    print(ensure())
