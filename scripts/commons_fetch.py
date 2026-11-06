#!/usr/bin/env python3
"""Fetch landmark photos from Wikimedia Commons (runs inside GitHub Actions).

For every commons-requests/<name>.txt without a matching photos/<name>/.done:
  each non-empty line is a search query, e.g.  "Oriole Park at Camden Yards"
  optional "| N" suffix = how many candidates to keep for that query (default 3)
Downloads up to N good candidates per query (2400px wide JPEG renditions) into
photos/<name>/ and writes manifest.tsv with:
  file <TAB> query <TAB> commons title <TAB> license <TAB> artist <TAB> needs_credit
Only freely licensed files are kept (public domain, CC0, CC BY, CC BY-SA).
"""
import glob, html, json, os, re, sys, time, urllib.parse, urllib.request

UA = "CityShortsBot/1.0 (https://github.com/stevenbendler2-beep/City-shorts)"
API = "https://commons.wikimedia.org/w/api.php"
OK_LICENSES = re.compile(r"^(public domain|pd|cc0|cc[- ]by(-sa)?[- ]?\d?(\.\d)?)", re.I)


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    for i in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except Exception as e:  # retry politely
            print("retry", url[:120], e, file=sys.stderr); time.sleep(3 * (i + 1))
    raise RuntimeError("failed " + url)


def strip(s):
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", s or ""))).strip()


def search(query, limit=12):
    p = {"action": "query", "format": "json", "generator": "search", "gsrnamespace": 6,
         "gsrsearch": f"{query} filetype:bitmap", "gsrlimit": limit, "prop": "imageinfo",
         "iiprop": "url|size|mime|extmetadata", "iiurlwidth": 2400}
    data = json.loads(get(API + "?" + urllib.parse.urlencode(p)))
    pages = sorted((data.get("query") or {}).get("pages", {}).values(), key=lambda x: x.get("index", 99))
    out = []
    for pg in pages:
        ii = (pg.get("imageinfo") or [{}])[0]
        if ii.get("mime") not in ("image/jpeg", "image/png"): continue
        if min(ii.get("width", 0), ii.get("height", 0)) < 900: continue
        md = ii.get("extmetadata", {})
        lic = strip(md.get("LicenseShortName", {}).get("value", ""))
        if not OK_LICENSES.match(lic): continue
        needs_credit = not re.match(r"^(public domain|pd|cc0)", lic, re.I)
        out.append(dict(title=pg["title"], url=ii.get("thumburl") or ii["url"], license=lic,
                        artist=strip(md.get("Artist", {}).get("value", ""))[:120] or "unknown",
                        desc=strip(md.get("ImageDescription", {}).get("value", ""))[:160],
                        needs_credit=needs_credit))
    # prefer files that need no credit, keep search order otherwise
    return sorted(out, key=lambda c: c["needs_credit"])


def main():
    for req in sorted(glob.glob("commons-requests/*.txt")):
        name = os.path.splitext(os.path.basename(req))[0]
        d = os.path.join("photos", name)
        if os.path.exists(os.path.join(d, ".done")): continue
        os.makedirs(d, exist_ok=True)
        rows, i = [], 0
        for line in open(req, encoding="utf-8"):
            line = line.strip()
            if not line or line.startswith("#"): continue
            q, _, n = line.partition("|")
            q, n = q.strip(), int(n.strip() or 3)
            try:
                cands = search(q)[:n]
            except Exception as e:
                print("search failed", q, e, file=sys.stderr); continue
            if not cands: print("no free photos for:", q)
            for c in cands:
                i += 1
                slug = re.sub(r"[^a-z0-9]+", "-", q.lower()).strip("-")[:40]
                f = f"{i:02d}-{slug}.jpg"
                try:
                    open(os.path.join(d, f), "wb").write(get(c["url"]))
                except Exception as e:
                    print("download failed", c["url"], e, file=sys.stderr); i -= 1; continue
                rows.append("\t".join([f, q, c["title"], c["license"], c["artist"], "yes" if c["needs_credit"] else "no"]))
                time.sleep(0.5)
        with open(os.path.join(d, "manifest.tsv"), "w", encoding="utf-8") as m:
            m.write("file\tquery\tcommons_title\tlicense\tartist\tneeds_credit\n" + "\n".join(rows) + "\n")
        open(os.path.join(d, ".done"), "w").close()
        print(f"{name}: {len(rows)} photos")


if __name__ == "__main__":
    main()
