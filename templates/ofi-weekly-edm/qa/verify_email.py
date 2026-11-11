#!/usr/bin/env python3
"""Post-build QA for an Atlas email. Run before delivering ANY change, however small.

Checks:
  1. Mobile CSS class parity — every button class in the body has a media-query rule.
     A new button class without one inherits Stripo's blanket mobile rule and renders
     as a fat boxed button on phones while looking correct on desktop.
  2. XHTML well-formedness (Stripo importer).
  3. Table balance — catches a structural edit that orphaned a wrapper tag.
  4. HTTP status of every link and image.
  5. File size against Gmail's ~102 KB clipping threshold.

These are STRUCTURAL checks. They cannot tell you what the email looks like —
still recommend a mobile preview before send when layout changed.

Usage:
    python verify_email.py file.html [--no-net]
"""

import re
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor


def styles_of(html):
    return "".join(re.findall(r"<style[^>]*>(.*?)</style>", html, re.S))


def check_button_parity(html):
    styles = styles_of(html)
    used = sorted(set(re.findall(r'class="es-button es-button-(\d+)"', html)))
    missing = [c for c in used if f"es-button-{c}" not in styles]
    return used, missing


def check_xhtml(html):
    try:
        from lxml import etree
        etree.fromstring(html.replace("&nbsp;", "&#160;").encode(),
                         etree.XMLParser(resolve_entities=False))
        return True, ""
    except Exception as e:
        return False, str(e).split("\n")[0]


BOT_BLOCKED = ("linkedin.com", "instagram.com", "facebook.com", "x.com", "twitter.com")


def check_urls(html, workers=4):
    """Atlas rate-limits concurrency (503s) and social sites bot-block (999/429/403),
    so retry any non-200 once, serially, before calling it a failure."""
    import time
    urls = set(re.findall(r'href="(https?://[^"]+)"', html))
    urls |= set(re.findall(r'<img[^>]+src="(https?://[^"]+)"', html))

    def status(u):
        r = subprocess.run(
            ["curl", "-sL", "--max-time", "20", "-A", "Mozilla/5.0", "-o", "/dev/null",
             "-w", "%{http_code}", u.replace("&amp;", "&")],
            capture_output=True, text=True)
        return r.stdout.strip()

    with ThreadPoolExecutor(workers) as ex:
        results = dict(zip(urls, ex.map(status, urls)))

    for u, c in list(results.items()):
        if c != "200":
            time.sleep(1.0)
            results[u] = status(u)

    bad, blocked = [], []
    for u, c in results.items():
        if c == "200":
            continue
        (blocked if any(d in u for d in BOT_BLOCKED) else bad).append((u, c))
    return results, bad, blocked


def main():
    path = sys.argv[1]
    net = "--no-net" not in sys.argv
    html = open(path).read()
    fail = False

    used, missing = check_button_parity(html)
    if missing:
        fail = True
        print(f"FAIL  button parity — no mobile rule for: {', '.join(missing)}")
        print("      add a rule alongside its siblings, e.g.")
        print("      a.es-button.es-button-XXXX { padding:5px 0!important; font-size:11px!important }")
    else:
        print(f"OK    button parity — {len(used)} classes, all have mobile rules")

    ok, err = check_xhtml(html)
    print("OK    XHTML well-formed" if ok else f"FAIL  XHTML — {err}")
    fail |= not ok

    o, c = html.count("<table"), html.count("</table>")
    print(f"{'OK   ' if o == c else 'FAIL '} tables {o}/{c}")
    fail |= o != c

    kb = round(len(html) / 1024, 1)
    print(f"{'OK   ' if kb <= 102 else 'WARN '} size {kb} KB (Gmail clips ~102 KB)")

    if net:
        results, bad, blocked = check_urls(html)
        if blocked:
            print(f"NOTE  {len(blocked)} social links bot-blocked (not a fault): "
                  + ", ".join(c for _, c in blocked))
        if bad:
            fail = True
            print(f"FAIL  {len(bad)}/{len(results)} URLs not 200:")
            for u, code in bad[:20]:
                print(f"      {code}  {u[:100]}")
        else:
            print(f"OK    {len(results) - len(blocked)} links and images all 200")

    print("\nStructural checks only — preview on mobile before send if layout changed.")
    sys.exit(1 if fail else 0)


if __name__ == "__main__":
    main()
