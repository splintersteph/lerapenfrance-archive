#!/usr/bin/env python3
"""Construit le site d'archive LREF a partir de lerapenfrance-archive.json.
Usage : python3 build.py archive.json sortie/
"""
import json, re, sys, os, html, unicodedata, shutil
from urllib.parse import unquote
from collections import Counter, defaultdict

SRC, OUT = sys.argv[1], sys.argv[2]
HERE = os.path.dirname(os.path.abspath(__file__))
MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août",
        "septembre", "octobre", "novembre", "décembre"]
WB = "https://web.archive.org/web/2020im_/"

data = json.load(open(SRC, encoding="utf-8"))
items = data["items"]
# corrige les adresses redirigees : le chemin reel est celui de la copie d'archive
for _i in items:
    _m = re.search(r"/web/\d+/https?://(?:www\.)?lerapenfrance\.fr(?::80)?(/[^?#]*)", _i.get("archive") or "")
    if _m and _m.group(1).strip("/") and _m.group(1).strip("/").split("/")[0].lower() != (_i.get("path") or "").strip("/").lower():
        _i["path"] = "/" + _m.group(1).strip("/").split("/")[0]
# correctifs manuels (pages mal redirigees dans l'archive)
_pf = os.path.join(os.path.dirname(os.path.abspath(SRC)), "patch-80-71.html")
if os.path.exists(_pf):
    items.append({"path": "/100-meilleurs-albums-annees-2000-de-80-a-71", "title": "Les 100 meilleurs albums des années 2000 : de 80 à 71",
                  "date": "2019-07-29T15:51:27+00:00", "author": "", "cats": ["Sélections", "Tops"], "tags": [],
                  "image": "http://lerapenfrance.fr/wp-content/uploads/2019/06/80-71.jpg", "desc": "Les années 2000 sont un paradoxe étrange dans le rap français.",
                  "archive": "https://web.archive.org/web/20210116023114/http://lerapenfrance.fr/100-meilleurs-albums-annees-2000-de-80-a-71/",
                  "html": open(_pf, encoding="utf-8").read()})


def slugify(s):
    s = unquote(s).strip("/")
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower()
    return s or "page"


def fdate(iso):
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", iso or "")
    if not m:
        return iso or "", ""
    y, mo, d = m.groups()
    return f"{int(d)} {MOIS[int(mo) - 1]} {y}", y


def esc(s):
    return html.escape(s or "", quote=True)


def clean_title(t):
    return re.sub(r"\s*[-–|]\s*(LREF|Le Rap [Ee]n France)\s*$", "", (t or "").strip())


# --- articles -------------------------------------------------------------
arts = [i for i in items if not i.get("special") and i.get("html")
        and re.match(r"\d{4}-\d{2}-\d{2}", i.get("date") or "")
        and not re.fullmatch(r"\d+|Mise en page \d+|Politique vie priv.*|Contact\.?", (i.get("title") or "").strip())]
seen = {}
for a in arts:
    a["title"] = clean_title(a["title"])
    a["slug"] = slugify(a["path"])
    a["fdate"], a["year"] = fdate(a.get("date"))
    a["rub"] = a["cats"][0] if a.get("cats") else "Divers"
# dedoublonnage (meme slug ou meme titre+date)
uniq = {}
for a in arts:
    k = a["slug"]
    if k not in uniq or len(a["html"]) > len(uniq[k]["html"]):
        uniq[k] = a
_h = {}
for a in list(uniq.values()):
    k = hash(a["html"])
    if k in _h:
        uniq.pop(a["slug"] if len(a["slug"]) > len(_h[k]["slug"]) else _h[k]["slug"], None)
    else:
        _h[k] = a
arts = sorted(uniq.values(), key=lambda a: a.get("date") or "", reverse=True)
by_path = {slugify(a["path"]): a for a in arts}


def img_url(src):
    if not src:
        return ""
    src = src.replace("https://lerapenfrance.fr", "http://lerapenfrance.fr")
    if "lerapenfrance.fr" in src:
        return WB + src
    return src


from bs4 import BeautifulSoup


def yt_block(soup, vid, title=""):
    d = soup.new_tag("div", attrs={"class": "yt"})
    d.append(soup.new_tag("iframe", attrs={"src": f"https://www.youtube-nocookie.com/embed/{vid}", "loading": "lazy",
                                            "allowfullscreen": "", "title": title or "Vidéo"}))
    return d


def rewrite(h, depth):
    pre = "../" * depth
    soup = BeautifulSoup(h, "html.parser")
    # videos YouTube (lazy embeds WordPress)
    for m in soup.select('meta[itemprop="embedURL"]'):
        mm = re.search(r"youtube(?:-nocookie)?\.com/embed/([\w-]{6,})", m.get("content", ""))
        box = m.find_parent("div", attrs={"title": True}) or m.find_parent("div", attrs={"itemprop": "video"})
        if mm and box:
            box.replace_with(yt_block(soup, mm.group(1), box.get("title", "")))
    for p in soup.select("p[data-yt]"):
        p.replace_with(yt_block(soup, p["data-yt"]))
    for m in soup.find_all("meta"):
        m.decompose()
    for hr in soup.select("hr[data-page]"):
        hr.attrs = {"class": "page"}
    for img in soup.find_all("img"):
        img["src"] = img_url(img.get("src", ""))
        img["loading"] = "lazy"
        for k in ("decoding", "fetchpriority"):
            img.attrs.pop(k, None)
        par = img.parent
        if par.name == "a" and re.search(r"\.(jpe?g|png|gif|webp)$", par.get("href", ""), re.I):
            par.unwrap()
    for a in soup.find_all("a"):
        href = a.get("href", "")
        mm = re.match(r"https?://(?:www\.)?lerapenfrance\.fr(?::80)?(/[^?#]*)?", href)
        if mm:
            p = (mm.group(1) or "/").strip("/")
            s = slugify(p.split("/")[0]) if p else ""
            if not p and "?" not in href:
                a["href"] = pre + "index.html"
            elif s in by_path:
                a["href"] = f"{pre}a/{s}/"
            else:
                a["href"] = "https://web.archive.org/web/2020/" + href
        elif href.startswith("/"):
            a["href"] = "https://web.archive.org/web/2020/http://lerapenfrance.fr" + href
    for sp in soup.find_all("span"):
        sp.unwrap()
    for el in soup.find_all(["p", "div"]):
        if not el.get_text(strip=True).replace("\xa0", "") and not el.find(["img", "iframe"]):
            el.decompose()
    return str(soup)


def page(title, body, depth=0, desc="", active=""):
    pre = "../" * depth
    nav = [("index.html", "Accueil", "home"), ("articles.html", "Tous les articles", "arts"),
           ("top-100-annees-90.html", "Top 100 années 90", "t90"),
           ("top-100-annees-2000.html", "Top 100 années 2000", "t00"), ("a-propos.html", "À propos", "about")]
    links = "".join(f'<a href="{pre}{h}"{" class=on" if k == active else ""}>{t}</a>' for h, t, k in nav)
    return f"""<!DOCTYPE html>
<html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="stylesheet" href="{pre}style.css">
</head><body>
<header class="top"><div class="wrap">
<a class="logo" href="{pre}index.html"><span>LREF</span> Le Rap en France <em>· archives</em></a>
<nav>{links}</nav></div></header>
<main class="wrap">{body}</main>
<footer><div class="wrap">Le Rap en France (2011-2023) · Archive reconstituée à partir de la <a href="https://web.archive.org/">Wayback Machine</a>. Les textes appartiennent à leurs auteurs.</div></footer>
</body></html>"""


def write(rel, content):
    p = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w", encoding="utf-8").write(content)


if os.path.isdir(OUT):
    for f in os.listdir(OUT):
        if f in (".git", "CNAME", "tools", "data", "README.md", ".nojekyll"):
            continue
        fp = os.path.join(OUT, f)
        shutil.rmtree(fp) if os.path.isdir(fp) else os.remove(fp)
os.makedirs(OUT, exist_ok=True)
shutil.copy(os.path.join(HERE, "style.css"), os.path.join(OUT, "style.css")) if os.path.abspath(HERE) != os.path.abspath(OUT) else None
open(os.path.join(OUT, ".nojekyll"), "w").close()

# --- pages articles -------------------------------------------------------
for i, a in enumerate(arts):
    meta = " · ".join(x for x in [a["fdate"], ("par " + a["author"]) if a.get("author") else "", ", ".join(a["cats"])] if x)
    tags = "".join(f"<span>{esc(t)}</span>" for t in a.get("tags", []))
    cover = f'<img class="cover" src="{esc(img_url(a["image"]))}" alt="" loading="lazy">' if a.get("image") else ""
    prev_a = arts[i + 1] if i + 1 < len(arts) else None
    next_a = arts[i - 1] if i > 0 else None
    pn = '<nav class="pn">' + (f'<a href="../{prev_a["slug"]}/">← {esc(prev_a["title"])}</a>' if prev_a else "<span></span>") + \
         (f'<a href="../{next_a["slug"]}/">{esc(next_a["title"])} →</a>' if next_a else "<span></span>") + "</nav>"
    body = f"""<article class="post">
<p class="kicker">{esc(a["rub"])}</p>
<h1>{esc(a["title"])}</h1>
<p class="meta">{esc(meta)}</p>
{cover}
<div class="content">{rewrite(a["html"], 2)}</div>
{f'<p class="tags">{tags}</p>' if tags else ''}
<p class="src">Copie d'archive : <a href="{esc(a["archive"])}">voir la page d'origine sur la Wayback Machine</a></p>
{pn}
</article>"""
    write(f"a/{a['slug']}/index.html", page(a["title"] + " – LREF archives", body, 2, a.get("desc", ""), "arts"))

# --- index de recherche ----------------------------------------------------
idx = [{"s": a["slug"], "t": a["title"], "d": a.get("date", "")[:10], "f": a["fdate"], "a": a.get("author", ""),
        "r": a["rub"], "c": a["cats"], "x": (a.get("desc") or "")[:180]} for a in arts]
write("search.json", json.dumps(idx, ensure_ascii=False, separators=(",", ":")))

rubs = Counter(a["rub"] for a in arts)
years = Counter(a["year"] for a in arts if a["year"])
authors = Counter(a["author"] for a in arts if a.get("author"))

# --- liste filtrable -------------------------------------------------------
opts = lambda c: "".join(f'<option value="{esc(k)}">{esc(k)} ({n})</option>' for k, n in sorted(c.items(), key=lambda x: (-x[1], x[0])))
yopts = "".join(f'<option value="{y}">{y} ({n})</option>' for y, n in sorted(years.items(), reverse=True))
body = f"""<h1>Tous les articles</h1>
<div class="filters">
<input id="q" type="search" placeholder="Rechercher un artiste, un album, un titre…" autofocus>
<select id="r"><option value="">Toutes les rubriques</option>{opts(rubs)}</select>
<select id="y"><option value="">Toutes les années</option>{yopts}</select>
<select id="au"><option value="">Tous les auteurs</option>{opts(authors)}</select>
</div>
<p id="n" class="count"></p>
<ul id="list" class="list"></ul>
<script>
const norm=s=>(s||"").normalize("NFD").replace(/[\\u0300-\\u036f]/g,"").toLowerCase();
let D=[];const $=id=>document.getElementById(id);
const P=new URLSearchParams(location.search);["q","r","y","au"].forEach(k=>{{if(P.get(k))$(k).value=P.get(k)}});
function draw(){{const q=norm($("q").value),r=$("r").value,y=$("y").value,au=$("au").value;
const R=D.filter(a=>(!r||a.r===r)&&(!y||a.d.startsWith(y))&&(!au||a.a===au)&&(!q||norm(a.t+" "+a.a+" "+a.c.join(" ")+" "+a.x).includes(q)));
$("n").textContent=R.length+" article"+(R.length>1?"s":"");
$("list").innerHTML=R.slice(0,400).map(a=>`<li><a href="a/${{a.s}}/"><span class="lt">${{a.t}}</span><span class="lm">${{a.r}} · ${{a.f}}${{a.a?" · "+a.a:""}}</span></a></li>`).join("")+(R.length>400?"<li class=more>Affinez la recherche pour voir plus de résultats…</li>":"");}}
fetch("search.json").then(r=>r.json()).then(j=>{{D=j;draw()}});
["q","r","y","au"].forEach(k=>$(k).addEventListener("input",draw));
</script>"""
write("articles.html", page("Tous les articles – LREF archives", body, 0, "", "arts"))

# --- top 90 ----------------------------------------------------------------
JUNK = {"ARTIST", "SINGLE", "The Whistlespankers", "Nigel & Me", "Digital Love", "Follow the blink", "The Matadoors",
        "Oilspill", "Nostralus", "Extreme Water", "Fanfare", "Isolde", "Skyrunners", "No problem, Housten",
        "Insane Children", "Playground", "The Green Lords", "Bacteria Invasion"}
t90 = next((i for i in items if i.get("special") == "top90"), None)
entries = []
intro = ""
if t90:
    txt = t90["text"]
    mi = re.search(r"Top 100 / Années 90\s*\n(.+?)\n\s*100\s*\n", txt, re.S)
    intro = mi.group(1).strip() if mi else ""
    head, _, details = txt.partition("\n 100100") if "\n 100100" in txt else txt.partition("100100")
    lst = re.findall(r"\n\s*(\d{2,3})\s*\n([^\n]+)\n([^\n]+)", "\n" + head[head.find("Top 100"):])
    ranking = {int(n): (ar.strip(), al.strip()) for n, ar, al in lst if 1 <= int(n) <= 100}
    blocks = re.split(r"\n\s*(\d{1,3})100\s*\n", "\n 100100\n" + details.lstrip(" "))
    det = {}
    for k in range(1, len(blocks) - 1, 2):
        det[int(blocks[k])] = blocks[k + 1]
    for n in range(1, 101):
        ar, al = ranking.get(n, ("", ""))
        b = det.get(n, "")
        lines = [l.strip() for l in b.split("\n") if l.strip()]
        year = next((l for l in lines[:8] if re.fullmatch(r"\d{4}", l)), "")
        key = al.lower()[:12]
        start = 0
        for j, l in enumerate(lines[:10]):
            if (key and key in l.lower() and (" - " in l or " – " in l or "—" in l or "(Compilation)" in l)) or "(Compilation)" in l:
                start = j + 1
                break
        else:
            start = next((j + 1 for j, l in enumerate(lines[:10]) if re.fullmatch(r"\d{4}", l)), 0)
            while start < len(lines) and (lines[start] in JUNK or lines[start] in (ar, al)):
                start += 1
        desc = [l for l in lines[start:] if l not in JUNK]
        entries.append((n, ar, al, year, desc))


def para(l):
    l = esc(l)
    l = re.sub(r"^(Pourquoi cet album \?|Le morceau qu[’']on recommande\s*[:?]?)", r"<strong>\1</strong>", l)
    return f"<p>{l}</p>"


rows = "".join(f'<li><a href="#n{n}"><b>{n}</b> {esc(ar)} – <i>{esc(al)}</i></a></li>' for n, ar, al, y, d in entries)
cards = "".join(f'<section class="album" id="n{n}"><div class="num">{n}</div><div><h2>{esc(ar)} <span>– {esc(al)}</span></h2>'
                f'{"".join(para(l) for l in d)}</div></section>' for n, ar, al, y, d in reversed(entries))
body = f"""<h1>Top 100 – Années 90</h1><p class="lead">{esc(intro)}</p>
<details class="toc" open><summary>Le classement</summary><ol class="rank" reversed>{rows}</ol></details>{cards}"""
write("top-100-annees-90.html", page("Top 100 des années 90 – LREF archives", body, 0, intro[:150], "t90"))

# --- top 2000 --------------------------------------------------------------
tranches = [a for a in arts if re.search(r"100-meilleurs-albums.*annees-2000", a["slug"])]
order = lambda a: -int((re.search(r"de-(\d+)-a", a["slug"]) or re.search(r"(10)$", "10")).group(1)) if "top-10" not in a["slug"] else -10
tranches.sort(key=order)
rank00 = []
for a in tranches:
    for el in BeautifulSoup(a["html"], "html.parser").find_all(["h1", "h2", "h3", "h4", "strong", "b"]):
        m = re.match(r"\s*#?(\d{1,3})\s*[–-]\s*(.+?)\s*\((\d{4})\)\s*$", el.get_text(" ").replace("\xa0", " "))
        if m:
            rank00.append((int(m.group(1)), re.sub(r"\s+", " ", m.group(2)).replace(" ’", "’"), m.group(3), a["slug"]))
rank00 = sorted({r[0]: r for r in rank00}.values())
lst = "".join(f'<li><a href="a/{s}/"><b>{n}</b> {esc(t)} <span class="y">({y})</span></a></li>' for n, t, y, s in rank00)
trs = "".join(f'<li><a href="a/{a["slug"]}/">{esc(a["title"])}</a></li>' for a in sorted(tranches, key=order, reverse=False))
body = f"""<h1>Top 100 – Années 2000</h1>
<p class="lead">Classement établi avec 43 votants (rédactions de L'Abcdr du Son, Reaphit, Le Bon Son, Revrse, SURL, ainsi que Genono, Spleenter et Olivier Cachin). Chacun classait 50 albums, de 50 points pour le premier à 1 point pour le cinquantième.</p>
<div class="two"><ol class="rank">{lst}</ol><div><h2>Les articles</h2><ul class="plain">{trs}</ul></div></div>"""
write("top-100-annees-2000.html", page("Top 100 des années 2000 – LREF archives", body, 0, "", "t00"))

# --- accueil ---------------------------------------------------------------
def card(a):
    im = f'<img src="{esc(img_url(a["image"]))}" alt="" loading="lazy">' if a.get("image") else '<div class="ph">LREF</div>'
    return f'<a class="card" href="a/{a["slug"]}/">{im}<span class="k">{esc(a["rub"])}</span><span class="t">{esc(a["title"])}</span><span class="m">{esc(a["fdate"])}</span></a>'

rubl = "".join(f'<a href="articles.html?r={esc(k)}">{esc(k)} <b>{n}</b></a>' for k, n in rubs.most_common(14))
yl = "".join(f'<a href="articles.html?y={y}">{y} <b>{n}</b></a>' for y, n in sorted(years.items()))
body = f"""<section class="hero"><h1>Le Rap en France</h1>
<p>{len(arts)} articles sauvés du site LREF : chroniques, interviews, focus, dossiers, classements. Fondé en 2011, le site a disparu après un piratage ; tout ce qui suit a été reconstitué à partir des copies de la Wayback Machine.</p>
<form action="articles.html"><input name="q" type="search" placeholder="Chercher un artiste, un album…"><button>Rechercher</button></form></section>
<section class="tops"><a href="top-100-annees-90.html"><span>Classement</span>Top 100<br>années 90</a><a href="top-100-annees-2000.html"><span>Classement</span>Top 100<br>années 2000</a></section>
<h2 class="sec">Rubriques</h2><div class="chips">{rubl}</div>
<h2 class="sec">Par année</h2><div class="chips">{yl}</div>
<h2 class="sec">Derniers articles publiés</h2><div class="grid">{"".join(card(a) for a in arts[:12])}</div>
<p class="all"><a href="articles.html">Voir les {len(arts)} articles →</a></p>"""
write("index.html", page("Le Rap en France – archives", body, 0, "Archive du site Le Rap en France (LREF)", "home"))

body = f"""<h1>À propos</h1><div class="content">
<p>Le Rap en France (LREF) était un média web consacré au rap français, fondé en 2011 par Stéphane Fortems. Le site a réuni jusqu'à une trentaine de contributeurs bénévoles, publié un magazine papier bimestriel et atteint environ 1,5 million de pages vues.</p>
<p>Le site a été perdu à la suite d'un piratage et son nom de domaine a depuis changé de mains. Cette archive rassemble les {len(arts)} articles dont une copie a été conservée par la <a href="https://web.archive.org/">Wayback Machine</a> d'Internet Archive. Les images sont chargées depuis ces copies d'archive, certaines peuvent donc manquer. Les années 2011 à 2015 sont moins bien couvertes, car l'archive a peu indexé le site à cette période.</p>
<p>Chaque article renvoie vers sa copie d'origine sur la Wayback Machine.</p></div>"""
write("a-propos.html", page("À propos – LREF archives", body, 0, "", "about"))
write("404.html", page("Page introuvable – LREF archives", '<h1>Page introuvable</h1><p><a href="/lerapenfrance-archive/">Retour à l’accueil</a></p>'))

print(f"{len(arts)} articles · rubriques {len(rubs)} · top90 {len(entries)} · top00 {len(rank00)} · années {dict(sorted(years.items()))}")
