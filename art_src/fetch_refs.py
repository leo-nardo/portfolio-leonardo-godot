"""Baixa imagens de referência (só para estudo; não entram no jogo) das wikis de fãs."""
import json, re, sys, urllib.parse, urllib.request
from pathlib import Path

OUT = Path(__file__).resolve().parent.parent / "referencias" / "imagens"
UA = {"User-Agent": "Mozilla/5.0 (reference study)"}

def api(wiki, **p):
    p["format"] = "json"
    url = f"https://{wiki}.fandom.com/api.php?" + urllib.parse.urlencode(p)
    return json.load(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=30))

def search(wiki, q, n):
    r = api(wiki, action="query", list="search", srsearch=q, srnamespace=6, srlimit=n)
    return [s["title"] for s in r["query"]["search"]]

def url_of(wiki, title):
    r = api(wiki, action="query", titles=title, prop="imageinfo", iiprop="url|size", iiurlwidth=1600)
    for pg in r["query"]["pages"].values():
        ii = pg.get("imageinfo")
        if ii:
            return ii[0].get("thumburl") or ii[0]["url"]
    return None

plan = [
    ("adventuretime", "AT", ["S7e17 Finn model-sheet.png", "S7e17 Jake model-sheet.png", "Modelsheet - Wanderingbaldman.jpg", "Modelsheet - Archerdan.jpg", "Modelsheet - Ancientscholar.jpg"]),
    ("regularshow", "RS", ["S1E05.082 M&R walking through woods.png", "S6E04.199 Everyone Walking in the Woods.png", "S6E05.010 Muscle Man Walking Away.png", "Incidental Janet Model Sheet.jpeg", "Stag-Man Model Sheet.JPG"]),
]
searches = [("adventuretime", "AT", "background forest", 6), ("adventuretime", "AT", "tree fort", 5), ("adventuretime", "AT", "Finn Jake walking", 5),
            ("regularshow", "RS", "background park", 6), ("regularshow", "RS", "mordecai rigby walking", 5), ("regularshow", "RS", "treehouse", 3)]
items = []
for wiki, tag, titles in plan:
    for t in titles:
        items.append((wiki, tag, "File:" + t))
for wiki, tag, q, n in searches:
    try:
        for t in search(wiki, q, n):
            items.append((wiki, tag, t))
    except Exception as e:
        print("busca falhou", q, e)
seen, count = set(), 0
for wiki, tag, title in items:
    if title in seen or count >= 30:
        continue
    seen.add(title)
    try:
        u = url_of(wiki, title)
        if not u:
            continue
        ext = ".png" if ".png" in u.lower() else ".jpg"
        name = tag + "_" + re.sub(r"[^A-Za-z0-9]+", "_", title.replace("File:", "").rsplit(".", 1)[0])[:60] + ext
        data = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=60).read()
        if len(data) < 15000:
            continue
        (OUT / name).write_bytes(data)
        count += 1
        print(f"{count:2d} {name} {len(data)//1024} KB  <- {wiki}.fandom.com {title}")
        with open(OUT.parent / "FONTES.md", "a", encoding="utf-8") as f:
            f.write(f"- {name} — {wiki}.fandom.com — {title}\n")
    except Exception as e:
        print("falhou", title, e)
print("total", count)
