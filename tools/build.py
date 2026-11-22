#!/usr/bin/env python3
"""Construit le site d'archive LREF (Le Rap en France).
Usage : python3 tools/build.py data/lerapenfrance-archive.json .
"""
import json, re, sys, os, html, unicodedata, shutil
from urllib.parse import unquote, quote
from collections import Counter, defaultdict
from bs4 import BeautifulSoup
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from corrections import corrige_html, corrige_texte, est_spam, retire_paragraphes_spam

SRC, OUT = sys.argv[1], sys.argv[2]
HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.dirname(os.path.abspath(SRC))
MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août",
        "septembre", "octobre", "novembre", "décembre"]
WB = "https://web.archive.org/web/2020im_/"
BASE = "/"

SECTIONS = [
    ("classements", "Classements", ["Tops", "Top 100 années 2000", "Top années 90"],
     "Les tops de la rédaction : albums de l'année, beatmakers, décennies."),
    ("dossiers", "Dossiers", ["Dossiers", "Articles à thèmes", "Focus sur", "Décryptage", "A l'origine",
                              "L'exégèse rapologique", "Le rap français et ...", "Cartes du rap français",
                              "Tour de France rapologique", "Médias"],
     "Les grands formats : enquêtes, analyses, portraits et explications de textes."),
    ("interviews", "Interviews", ["Interviews", "Radio - Une heure avec ...", "Radio"],
     "Rappeurs, beatmakers, DJ et acteurs du milieu, au micro de LREF."),
    ("chroniques", "Chroniques", ["Chroniques", "Live report", "Grands classiques", "Explications d'albums",
                                  "Projets récents"],
     "Albums, EP, mixtapes et concerts passés au crible."),
    ("billets", "Billets d'humeur", ["Billets d'humeur", "Articles versifiés"],
     "Coups de gueule, coups de cœur et lettres ouvertes."),
    ("selections", "Sélections", ["Sélections", "Découvertes", "Beatmakers", "Mes 5 films", "Mes 5 livres",
                                  "Mes 5...", "Mes 5 classiques", "Anadiplose de featurings", "Lecture aléatoire",
                                  "Bienvenueaustud"],
     "Découvertes, playlists et les « Mes 5 » des artistes."),
    ("actus", "Actus", ["Actus", "En Bref", "Une semaine de rap français", "Evénements", "Vidéos", "Magazine"],
     "Les revues de la semaine, les festivals et l'actualité : le rap français raconté au fil de l'eau."),
]
SEC = {s[0]: s for s in SECTIONS}
SEC_LABEL = {s[0]: s[1] for s in SECTIONS}
SEC_LABEL["divers"] = "Divers"

data = json.load(open(SRC, encoding="utf-8"))
items = data["items"]

# --- corrections de l'extraction -----------------------------------------
for _i in items:
    _m = re.search(r"/web/\d+/https?://(?:www\.)?lerapenfrance\.fr(?::80)?(/[^?#]*)", _i.get("archive") or "")
    if _m and _m.group(1).strip("/") and _m.group(1).strip("/").split("/")[0].lower() != (_i.get("path") or "").strip("/").lower():
        _i["path"] = "/" + _m.group(1).strip("/").split("/")[0]
_pf = os.path.join(DATA, "patch-80-71.html")
if os.path.exists(_pf):
    items.append({"path": "/100-meilleurs-albums-annees-2000-de-80-a-71", "title": "Les 100 meilleurs albums des années 2000 : de 80 à 71",
                  "date": "2019-07-29T15:51:27+00:00", "author": "", "cats": ["Sélections", "Tops"], "tags": [],
                  "image": "http://lerapenfrance.fr/wp-content/uploads/2019/06/80-71.jpg",
                  "desc": "Les années 2000 sont un paradoxe étrange dans le rap français.",
                  "archive": "https://web.archive.org/web/20210116023114/http://lerapenfrance.fr/100-meilleurs-albums-annees-2000-de-80-a-71/",
                  "html": open(_pf, encoding="utf-8").read()})


# articles recuperes depuis des copies anterieures au piratage
_rf = os.path.join(DATA, "recovered.json")
RECOVERED = json.load(open(_rf, encoding="utf-8")) if os.path.exists(_rf) else []
_rec_paths = {r["path"] for r in RECOVERED}
_old = {i.get("path"): i for i in items}
for r in RECOVERED:
    o = _old.get(r["path"], {})
    if not r.get("date"):
        r["date"] = o.get("date", "")
    if not r.get("cats"):
        r["cats"] = o.get("cats", [])
items = [i for i in items if i.get("path") not in _rec_paths] + RECOVERED
SPAM_RETIRES = []


def slugify(s):
    s = unquote(s).strip("/")
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-zA-Z0-9]+", "-", s).strip("-").lower() or "page"


def fdate(iso):
    m = re.match(r"(\d{4})-(\d{2})-(\d{2})", iso or "")
    if not m:
        return "", ""
    y, mo, d = m.groups()
    return f"{int(d)}{'er' if d == '01' else ''} {MOIS[int(mo) - 1]} {y}", y


def esc(s):
    return html.escape(s or "", quote=True)


def num(n):
    return f"{n:,}".replace(",", " ")


def clean_title(t):
    t = re.sub(r"\s*[-–|]\s*(LREF|Le Rap [Ee]n France)\s*$", "", (t or "").strip())
    return t.strip()


def section_of(cats):
    for key, _, cs, _ in SECTIONS:
        if any(c in cs for c in cats or []):
            return key
    return "divers"


def plain(h, n=None):
    soup = BeautifulSoup(h or "", "html.parser")
    for el in soup.find_all(["p", "h1", "h2", "h3", "h4", "li", "br", "div", "blockquote", "figure", "td"]):
        el.append(" ")
    for el in soup.find_all(["script", "style", "iframe", "figcaption"]):
        el.decompose()
    t = re.sub(r"\s+", " ", soup.get_text("")).strip()
    t = re.sub(r"\s+([,.)])", r"\1", t)
    return t[:n] if n else t


# --- articles -------------------------------------------------------------
arts = [i for i in items if not i.get("special") and i.get("html")
        and re.match(r"\d{4}-\d{2}-\d{2}", i.get("date") or "")
        and not re.fullmatch(r"\d+|Mise en page \d+|Politique vie priv.*|Contact\.?", (i.get("title") or "").strip())]
_clean = []
STATS = Counter()
for a in arts:
    _s = BeautifulSoup(a["html"], "html.parser")
    if est_spam(_s.get_text(" ")):
        _n = retire_paragraphes_spam(_s)
        if est_spam(_s.get_text(" ")) or len(_s.get_text(" ").split()) < 40:
            SPAM_RETIRES.append(a["path"])
            continue
        STATS["paragraphes de spam"] += _n
    else:
        STATS["paragraphes de spam"] += retire_paragraphes_spam(_s)
    a["html"] = str(corrige_html(_s, STATS))
    _clean.append(a)
arts = _clean
for a in arts:
    a["title"] = clean_title(corrige_texte(a["title"], Counter()))
    a["slug"] = slugify(a["path"])
    a["fdate"], a["year"] = fdate(a["date"])
    a["sec"] = section_of(a.get("cats"))
uniq = {}
for a in arts:
    if a["slug"] not in uniq or len(a["html"]) > len(uniq[a["slug"]]["html"]):
        uniq[a["slug"]] = a
seen = {}
for a in sorted(uniq.values(), key=lambda a: (a["slug"].startswith("p-"), len(a["slug"]))):
    k = (re.sub(r"[^a-z0-9]", "", unicodedata.normalize("NFKD", a["title"].lower()).encode("ascii", "ignore").decode()), a["date"][:10])
    k2 = hash(a["html"])
    if k in seen or k2 in seen:
        uniq.pop(a["slug"], None)
    else:
        seen[k] = seen[k2] = 1
arts = sorted(uniq.values(), key=lambda a: a["date"], reverse=True)
# brèves retirées : « En Bref » de moins de 500 mots, concours et annonces promotionnelles
# annonces promotionnelles d'événements (festivals, soirées, line-ups), retirées à la demande de Stéphane
PROMO = {"mama-festival-2021-une-programmation-rap", "evenement-mama-festival-premier-apercu-programmation-2020",
         "mama-festival-defricheur-de-nouveaux-talent", "evenement-rock-seine-2019-toujours-plus-de-rap-francais",
         "evenement-nuits-secretes-fetent-leurs-18-ans", "evenement-lollapalooza-ledition-2019-signe-de-gastronomie-francaise",
         "marsatac-nouvelle-edition-sannonce-bouillante", "evenement-contre-culture-soiree-secoue-scene-underground",
         "breve-dour-vend-reve-ledition-2019", "evenements-magnifique-society-festival-porte-bien-nom",
         "evenements-n-m-novator-rap-rentre-t-grande-chanson-francaise", "decouvrez-futur-soirees-hip-hop-a-paris-cuniculaire",
         "hip-hop-is-red-festival-gratuit-fin-janvier", "evenement-decouvrez-laffiche-de-finale-buzz-booster-idf",
         "jeu-concours-hornet-frappe-a-cigale-7-decembre-2018", "evenement-ne-manquez-demi-finale-de-buzz-booster-idf",
         "alaclair-ensemble-a-conquete-de-paris", "mama-festival-artistes-hip-hop-de-9e-edition",
         "marsatac-15-16-17-juin-2018-20-ans", "breve-paris-hip-hop-festival-premiers-noms", "ne-loupez-release-party-colere-calme",
         "annonce-rap-france-recrute-2", "swift-guad-nouvel-album-pour-la-rentree", "clip-lma-seme-sa-premiere-graine",
         "clip-s-i-n-i-k-contradictions"}
BREVES = []
_keep = []
for a in arts:
    _w = len(BeautifulSoup(a["html"], "html.parser").get_text(" ").split())
    if ("En Bref" in a.get("cats", []) and _w < 500) \
            or re.match(r"\s*\[?(concours|chineurs du mois)", a["title"], re.I) \
            or ("Vidéos" in a.get("cats", []) and _w < 50) \
            or re.search(r"agenda des concerts|vade-mecum", a["title"], re.I) or a["slug"] == "summertime" or a["slug"] in PROMO:
        BREVES.append(a["slug"])
    else:
        _keep.append(a)
arts = _keep
# compte à rebours des tops 100 (« de 40 à 31 »…) : retirés, les classements complets vivent sur 90.lref.fr et 2000.lref.fr
COUNTDOWN = [a for a in arts if re.search(r"100 meilleurs albums", a["title"]) and re.search(r"\d+\s*à\s*\d+", a["title"])]
REDIRECT = {a["slug"]: ("top-100-annees-2000.html" if "2000" in a["title"] else "top-100-annees-90.html") for a in COUNTDOWN}
arts = [a for a in arts if a["slug"] not in REDIRECT]
TOPPAGES = json.load(open(os.path.join(os.path.dirname(SRC), "tops-pages.json"), encoding="utf-8"))
by_slug = {a["slug"]: a for a in arts}
for a in arts:
    a["text"] = plain(a["html"])
    t = a["text"]
    if len(t) <= 240:
        d = t
    else:
        cut = t[:240]
        end = max(cut.rfind(". "), cut.rfind("! "), cut.rfind("? "))
        d = cut[:end + 1] if end > 110 else re.sub(r"[\s,;:–-]+\S*$", "", cut) + "…"
    a["dek"] = d
    a["display"] = re.sub(r"^\s*\[[^\]]{1,45}\]\s*[:–-]?\s*", "", a["title"]) or a["title"]
    if a["display"] and a["display"][0].islower():
        a["display"] = a["display"][0].upper() + a["display"][1:]
    a["words"] = len(a["text"].split())


def img_url(src):
    if not src:
        return ""
    src = src.replace("https://lerapenfrance.fr", "http://lerapenfrance.fr").replace("http://www.lerapenfrance.fr", "http://lerapenfrance.fr")
    if "lerapenfrance.fr" in src:
        return WB + quote(src, safe=":/%?=&")
    return src


def yt_block(soup, vid, title=""):
    d = soup.new_tag("div", attrs={"class": "embed"})
    d.append(soup.new_tag("iframe", attrs={"src": f"https://www.youtube-nocookie.com/embed/{vid}", "loading": "lazy",
                                            "allowfullscreen": "", "title": title or "Vidéo"}))
    return d


def rewrite(h, depth):
    pre = "../" * depth
    soup = BeautifulSoup(h, "html.parser")
    for m in soup.select('meta[itemprop="embedURL"]'):
        mm = re.search(r"youtube(?:-nocookie)?\.com/embed/([\w-]{6,})", m.get("content", ""))
        box = m.find_parent("div", attrs={"title": True}) or m.find_parent("div", attrs={"itemprop": "video"})
        if mm and box:
            box.replace_with(yt_block(soup, mm.group(1), box.get("title", "")))
    for p in soup.select("p[data-yt]"):
        p.replace_with(yt_block(soup, p["data-yt"]))
    for a in soup.find_all("a", href=re.compile(r"flo\.uri\.sh/visualisation/\d+")):
        vid = re.search(r"visualisation/(\d+)", a["href"]).group(1)
        box = soup.new_tag("div", attrs={"class": "flourish"})
        box.append(soup.new_tag("iframe", attrs={"src": f"https://flo.uri.sh/visualisation/{vid}/embed", "loading": "lazy",
                                                  "title": "Carte interactive", "allowfullscreen": ""}))
        if vid == "10439095":
            p = soup.new_tag("p", attrs={"class": "embed-note"})
            l = soup.new_tag("a", href=pre + "jul-marseille.html")
            l.string = "Ouvrir la carte en grand, avec la liste des 87 lieux"
            p.append(l)
            box.append(p)
        (a.find_parent("p") or a).replace_with(box)
    for m in soup.find_all("meta"):
        m.decompose()
    for hr in soup.select("hr[data-page]"):
        hr.attrs = {"class": "page-break"}
    for img in soup.find_all("img"):
        img["src"] = img_url(img.get("src", ""))
        img["loading"] = "lazy"
        for k in ("decoding", "fetchpriority", "srcset", "sizes", "width", "height"):
            img.attrs.pop(k, None)
        par = img.parent
        if par.name == "a" and re.search(r"(\.(jpe?g|png|gif|webp)$|/attachment/|/\d+-\d+/?$)", par.get("href", ""), re.I):
            par.unwrap()
    for a in soup.find_all("a"):
        href = a.get("href", "")
        mm = re.match(r"https?://(?:www\.)?lerapenfrance\.fr(?::80)?(/[^?#]*)?", href)
        if mm:
            p = (mm.group(1) or "/").strip("/")
            s = slugify(p.split("/")[0]) if p else ""
            if not p and "?" not in href:
                a["href"] = pre + "index.html"
            elif s in by_slug:
                a["href"] = f"{pre}a/{s}/"
            elif s in REDIRECT:
                a["href"] = pre + REDIRECT[s]
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


# --- gabarit --------------------------------------------------------------
NAV = [(s[0], s[1]) for s in SECTIONS]


def page(title, body, depth=0, desc="", active="", og_image=""):
    pre = "../" * depth
    links = "".join(f'<a href="{pre}rubrique/{k}.html"{" aria-current=page" if k == active else ""}><i class="k-{k}"></i>{esc(t)}</a>' for k, t in NAV)
    return f"""<!DOCTYPE html>
<html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}">
{f'<meta property="og:image" content="{esc(og_image)}">' if og_image else ''}
<link rel="preload" href="{pre}fonts/Archivo.woff2" as="font" type="font/woff2" crossorigin>
<meta name="theme-color" content="#1E3350">
<link rel="stylesheet" href="{pre}style.css?v=5">
<script>document.addEventListener("error",e=>{{const t=e.target;if(t.tagName!=="IMG")return;const f=t.closest(".ph-host");if(f){{f.classList.add("noimg");t.remove()}}else t.remove()}},true);</script>
</head><body>
<a class="skip" href="#contenu">Aller au contenu</a>
<header class="bar"><a class="logo" href="{pre}index.html"><b>LREF</b><span>Fonds Le Rap en France</span></a>
<nav>{links}<a href="{pre}articles.html"{" aria-current=page" if active == "all" else ""}>Tout le fonds</a></nav>
<form action="{pre}articles.html" role="search"><input name="q" type="search" placeholder="Chercher dans le fonds" aria-label="Rechercher"></form></header>
<main id="contenu">{body}</main>
<footer class="ft"><div class="ft-in"><p class="ft-t">Provenance</p><p>Le Rap en France, média web consacré au rap français, fondé en 2011 par Stéphane Fortems. Le site a disparu après un piratage. Ce fonds a été reconstitué en 2026 à partir des copies conservées par la Wayback Machine d'Internet Archive. Les textes appartiennent à leurs auteurs.</p>
<p class="ft-l"><a href="https://90.lref.fr/">Top 100 années 90</a><a href="https://2000.lref.fr/">Top 100 années 2000</a><a href="https://albums.lref.fr/">Les albums de l'année</a><a href="https://2016.lref.fr/">Une année 2016</a><a href="{pre}a-propos.html">À propos du fonds</a><a href="{pre}jul-marseille.html">Jul &amp; Marseille, la carte</a></p></div></footer>
</body></html>"""


def write(rel, content):
    p = os.path.join(OUT, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, "w", encoding="utf-8").write(content)


KEEP = {".git", "CNAME", "tools", "data", "README.md", ".nojekyll"}
for f in os.listdir(OUT):
    if f in KEEP:
        continue
    fp = os.path.join(OUT, f)
    shutil.rmtree(fp) if os.path.isdir(fp) else os.remove(fp)
open(os.path.join(OUT, "style.css"), "w", encoding="utf-8").write(open(os.path.join(HERE, "style.css"), encoding="utf-8").read() + "\n" + open(os.path.join(HERE, "d.css"), encoding="utf-8").read())
shutil.copytree(os.path.join(HERE, "fonts"), os.path.join(OUT, "fonts"))
shutil.copytree(os.path.join(HERE, "vendor"), os.path.join(OUT, "vendor"))
open(os.path.join(OUT, ".nojekyll"), "w").close()


def byline(a, link=True, depth=0):
    pre = "../" * depth
    au = a.get("author")
    who = (f'<a href="{pre}articles.html?au={quote(au)}">{esc(au)}</a>' if link else esc(au)) if au else ""
    return f'{"Par " + who + ", le " if who else "Le "}<time datetime="{a["date"][:10]}">{esc(a["fdate"])}</time>'


def thumb(a, depth=0, cls=""):
    pre = "../" * depth
    im = f'<img src="{esc(img_url(a["image"]))}" alt="" loading="lazy">' if a.get("image") else ""
    return f'<span class="ph-host duo k-{a["sec"]} {cls}{"" if im else " noimg"}" data-k="{esc(SEC_LABEL[a["sec"]][:1])}">{im}</span>'


def card(a, depth=0, size="m", dek=True):
    pre = "../" * depth
    return f"""<article class="card card-{size}">
<a class="card-link" href="{pre}a/{a['slug']}/">{thumb(a, depth)}
<span class="kick k-{a['sec']}">{esc(SEC_LABEL[a['sec']])}</span>
<span class="card-title">{esc(a['display'])}</span></a>
{f'<p class="card-dek">{esc(a["dek"])}</p>' if dek else ''}
<p class="card-by">{byline(a, False)}</p></article>"""


def row(a, depth=0):
    pre = "../" * depth
    return f"""<li class="row"><a href="{pre}a/{a['slug']}/">{thumb(a, depth, "sm")}<span class="row-txt"><span class="row-title">{esc(a['display'])}</span><span class="row-meta">{esc(a.get('author') or '')}{', ' if a.get('author') else ''}{esc(a['fdate'])}</span></span></a></li>"""


# --- pages articles -------------------------------------------------------
by_sec = defaultdict(list)
for a in arts:
    by_sec[a["sec"]].append(a)
for i, a in enumerate(arts):
    same = [b for b in by_sec[a["sec"]] if b is not a and b.get("image")]
    idx = by_sec[a["sec"]].index(a)
    near = sorted(same, key=lambda b: abs(by_sec[a["sec"]].index(b) - idx))[:3]
    tags = "".join(f'<a href="../../articles.html?q={quote(t)}">{esc(t)}</a>' for t in a.get("tags", []) if t not in a.get("cats", []))
    cover = f'<figure class="cover"><img src="{esc(img_url(a["image"]))}" alt="" loading="eager"></figure>' if a.get("image") else ""
    mins = max(1, round(a["words"] / 230))
    body = f"""<article class="story">
<header class="story-head">
 <p class="kick k-{a['sec']}"><a href="../../rubrique/{a['sec'] if a['sec'] in SEC else 'actus'}.html">{esc(SEC_LABEL[a['sec']])}</a></p>
 <h1>{esc(a['display'])}</h1>
 <p class="story-by"><span>{byline(a, True, 2)}</span><span class="read">{mins} min de lecture</span></p>
</header>
{cover}
<div class="prose">{rewrite(a['html'], 2)}</div>
<footer class="story-foot">
 {f'<p class="tags"><span>Sujets</span>{tags}</p>' if tags else ''}
 <p class="src">Article publié sur lerapenfrance.fr. <a href="{esc(a['archive'])}">Voir la copie d'archive</a></p>
</footer>
</article>
{f'<section class="more"><h2>Dans la même rubrique</h2><div class="grid3">{"".join(card(b, 2, "s") for b in near)}</div></section>' if near else ''}"""
    write(f"a/{a['slug']}/index.html", page(a["title"] + " – Le Rap en France", body, 2, a["dek"], a["sec"], img_url(a.get("image", ""))))

# --- index de recherche ----------------------------------------------------
idx = [{"s": a["slug"], "t": a["display"], "d": a["date"][:10], "f": a["fdate"], "a": a.get("author", ""),
        "r": SEC_LABEL[a["sec"]], "k": a["sec"], "c": a.get("cats", []) + a.get("tags", []), "x": a["dek"][:160]} for a in arts]
write("search.json", json.dumps(idx, ensure_ascii=False, separators=(",", ":")))
years = Counter(a["year"] for a in arts)
authors = Counter(a["author"] for a in arts if a.get("author"))

# --- rubriques -------------------------------------------------------------
for key, label, _, blurb in SECTIONS:
    L = by_sec[key]
    with_img = [a for a in L if a.get("image")]
    top = with_img[:3] if len(with_img) >= 3 else L[:3]
    rest = [a for a in L if a not in top]
    ys = Counter(a["year"] for a in L)
    yl = "".join(f'<a href="#y{y}">{y}</a>' for y in sorted(ys, reverse=True))
    groups = defaultdict(list)
    for a in rest:
        groups[a["year"]].append(a)
    lists = "".join(f'<section class="yblock" id="y{y}"><h2 class="ytitle">{y}<span>{len(groups[y])} articles</span></h2><ul class="rows">{"".join(row(a, 1) for a in groups[y])}</ul></section>'
                    for y in sorted(groups, reverse=True))
    body = f"""<header class="sec-head k-{key}"><h1>{esc(label)}</h1><p>{esc(blurb)} {num(len(L))} articles.</p><nav class="yjump" aria-label="Années">{yl}</nav></header>
<div class="sec-top">{card(top[0], 1, "l") if top else ''}<div class="sec-top-side">{"".join(card(a, 1, "s") for a in top[1:])}</div></div>
{lists}"""
    write(f"rubrique/{key}.html", page(f"{label} – Le Rap en France", body, 1, blurb, key))

# --- recherche ---------------------------------------------------------------
opts = lambda c: "".join(f'<option value="{esc(k)}">{esc(k)} ({n})</option>' for k, n in sorted(c.items(), key=lambda x: (-x[1], x[0])))
sopts = "".join(f'<option value="{k}">{esc(l)}</option>' for k, l, _, _ in SECTIONS)
yopts = "".join(f'<option value="{y}">{y}</option>' for y in sorted(years, reverse=True))
body = f"""<header class="sec-head"><h1>Toutes les archives</h1><p>{num(len(arts))} articles publiés entre 2011 et 2023. Cherchez un artiste, un album, un auteur.</p></header>
<div class="finder">
<label class="sr" for="q">Rechercher</label><input id="q" type="search" placeholder="Rechercher…">
<label class="sr" for="r">Rubrique</label><select id="r"><option value="">Toutes les rubriques</option>{sopts}</select>
<label class="sr" for="y">Année</label><select id="y"><option value="">Toutes les années</option>{yopts}</select>
<label class="sr" for="au">Auteur</label><select id="au"><option value="">Tous les auteurs</option>{opts(authors)}</select>
</div>
<p id="n" class="count" aria-live="polite"></p>
<ul id="list" class="results"></ul>
<script>
const norm=s=>(s||"").normalize("NFD").replace(/[\\u0300-\\u036f]/g,"").toLowerCase();
const E=s=>(s||"").replace(/[&<>"]/g,c=>({{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}}[c]));
let D=[];const $=id=>document.getElementById(id);
const P=new URLSearchParams(location.search);["q","r","y","au"].forEach(k=>{{if(P.get(k))$(k).value=P.get(k)}});
function draw(){{const q=norm($("q").value),r=$("r").value,y=$("y").value,au=$("au").value;
const R=D.filter(a=>(!r||a.k===r)&&(!y||a.d.startsWith(y))&&(!au||a.a===au)&&(!q||norm(a.t+" "+a.a+" "+a.c.join(" ")+" "+a.x).includes(q)));
$("n").textContent=R.length?R.length+" article"+(R.length>1?"s":""):"Aucun article ne correspond. Essayez un autre mot ou retirez un filtre.";
$("list").innerHTML=R.slice(0,300).map(a=>`<li><a href="a/${{a.s}}/"><span class="kick k-${{a.k}}">${{E(a.r)}}</span><span class="res-title">${{E(a.t)}}</span><span class="res-dek">${{E(a.x)}}</span><span class="res-meta">${{a.a?E(a.a)+", ":""}}${{E(a.f)}}</span></a></li>`).join("")+(R.length>300?`<li class="more-res">Les 300 premiers résultats sont affichés. Précisez la recherche pour voir les autres.</li>`:"");}}
fetch("search.json").then(r=>r.json()).then(j=>{{D=j;draw()}});
["q","r","y","au"].forEach(k=>$(k).addEventListener("input",draw));
</script>"""
write("articles.html", page("Toutes les archives – Le Rap en France", body, 0, "", "all"))

# --- top 90 ----------------------------------------------------------------
JUNK = {"ARTIST", "SINGLE", "The Whistlespankers", "Nigel & Me", "Digital Love", "Follow the blink", "The Matadoors",
        "Oilspill", "Nostralus", "Extreme Water", "Fanfare", "Isolde", "Skyrunners", "No problem, Housten",
        "Insane Children", "Playground", "The Green Lords", "Bacteria Invasion"}
t90 = next((i for i in items if i.get("special") == "top90"), None)
entries, intro = [], ""
if t90:
    txt = t90["text"]
    mi = re.search(r"Top 100 / Années 90\s*\n(.+?)\n\s*100\s*\n", txt, re.S)
    intro = mi.group(1).strip() if mi else ""
    head, _, details = txt.partition("\n 100100") if "\n 100100" in txt else txt.partition("100100")
    lst = re.findall(r"\n\s*(\d{2,3})\s*\n([^\n]+)\n([^\n]+)", "\n" + head[head.find("Top 100"):])
    ranking = {int(n): (ar.strip(), al.strip()) for n, ar, al in lst if 1 <= int(n) <= 100}
    blocks = re.split(r"\n\s*(\d{1,3})100\s*\n", "\n 100100\n" + details.lstrip(" "))
    det = {int(blocks[k]): blocks[k + 1] for k in range(1, len(blocks) - 1, 2)}
    for n in range(1, 101):
        ar, al = ranking.get(n, ("", ""))
        lines = [l.strip() for l in det.get(n, "").split("\n") if l.strip()]
        key = al.lower()[:12]
        start = 0
        for j, l in enumerate(lines[:10]):
            if (key and key in l.lower() and (" - " in l or " – " in l or "—" in l)) or "(Compilation)" in l:
                start = j + 1
                break
        else:
            start = next((j + 1 for j, l in enumerate(lines[:10]) if re.fullmatch(r"\d{4}", l)), 0)
            while start < len(lines) and (lines[start] in JUNK or lines[start] in (ar, al)):
                start += 1
        entries.append((n, ar, al, [l for l in lines[start:] if l not in JUNK]))


def para(l):
    l = esc(l)
    l = re.sub(r"^(Pourquoi cet album \?|Le morceau qu[’']on recommande\s*[:?]?)", r"<strong>\1</strong>", l)
    return f"<p>{l}</p>"


rows90 = "".join(f'<li><a href="#n{n}"><span class="rk">{n}</span><span class="rk-a">{esc(ar)}</span><span class="rk-t">{esc(al)}</span></a></li>' for n, ar, al, d in entries)
cards90 = "".join(f'<section class="entry" id="n{n}"><p class="entry-n">{n}</p><div class="entry-b"><h2><span class="rk-a">{esc(ar)}</span> <span class="rk-t">{esc(al)}</span></h2>{"".join(para(l) for l in d)}</div></section>'
                  for n, ar, al, d in reversed(entries))
body = f"""<header class="feature-head"><p class="kick k-classements">Classement</p><h1>Les 100 meilleurs albums des années 90</h1><p class="standfirst">{esc(intro)}</p></header>
<div class="rank-wrap"><ol class="ranking">{rows90}</ol></div>
<div class="entries">{cards90}</div>"""
write("top-100-annees-90.html", page("Les 100 meilleurs albums des années 90 – Le Rap en France", body, 0, intro[:160], "classements"))

# --- top 2000 --------------------------------------------------------------
tranches = [a for a in arts + COUNTDOWN if re.search(r"100-meilleurs-albums.*annees-2000", a["slug"])]
rank00 = []
for a in tranches:
    for el in BeautifulSoup(a["html"], "html.parser").find_all(["h1", "h2", "h3", "h4", "strong", "b"]):
        m = re.match(r"\s*#?(\d{1,3})\s*[–-]\s*(.+?)\s*\((\d{4})\)\s*$", el.get_text(" ").replace("\xa0", " "))
        if m:
            rank00.append((int(m.group(1)), re.sub(r"\s+", " ", m.group(2)).replace(" ’", "’"), m.group(3), a["slug"]))
rank00 = sorted({r[0]: r for r in rank00}.values())


def split_t(t):
    p = re.split(r"\s+[–-]\s+", t, maxsplit=1)
    return (p[0], p[1]) if len(p) == 2 else (t, "")


rows00 = "".join(f'<li><a href="https://2000.lref.fr/a/{TOPPAGES["2000"].get(str(n), "")}"><span class="rk">{n}</span><span class="rk-a">{esc(split_t(t)[0])}</span><span class="rk-t">{esc(split_t(t)[1])} <span class="rk-y">{y}</span></span></a></li>' for n, t, y, s in rank00)
order = lambda a: 0 if "top-10" in a["slug"] else -int(re.search(r"de-(\d+)-a", a["slug"]).group(1))
trs = "".join(card(a, 0, "s", False) for a in sorted(tranches, key=order, reverse=True) if a["slug"] in by_slug)
body = f"""<header class="feature-head"><p class="kick k-classements">Classement</p><h1>Les 100 meilleurs albums des années 2000</h1>
<p class="standfirst">Un classement établi avec 43 votants : les rédactions de L'Abcdr du Son, Reaphit, Le Bon Son, Revrse et SURL, ainsi que Genono, Spleenter et Olivier Cachin. Chacun classait cinquante albums, de cinquante points pour le premier à un point pour le dernier.</p></header>
<div class="rank-wrap"><ol class="ranking">{rows00}</ol></div>
<section class="more"><h2>Le top 10, l'article</h2><div class="grid5">{trs}</div><p class="src">Chaque album du classement a sa notice complète sur <a href="https://2000.lref.fr/">2000.lref.fr</a>.</p></section>"""
write("top-100-annees-2000.html", page("Les 100 meilleurs albums des années 2000 – Le Rap en France", body, 0, "", "classements"))

# anciennes adresses du compte à rebours : redirection vers le classement complet
for _s, _t in REDIRECT.items():
    write(f"a/{_s}/index.html", f'<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8"><meta name="robots" content="noindex"><meta http-equiv="refresh" content="0; url=../../{_t}"><link rel="canonical" href="../../{_t}"><title>Redirection</title></head><body><p><a href="../../{_t}">Voir le classement complet</a></p></body></html>')

# --- Jul & Marseille -------------------------------------------------------
_jf = os.path.join(DATA, "jul-marseille.json")
if os.path.exists(_jf):
    write("jul-marseille.json", open(_jf, encoding="utf-8").read())
    write("jul-marseille.html", open(os.path.join(HERE, "jul.html"), encoding="utf-8").read())

# --- la une ----------------------------------------------------------------
def pick(slug):
    return by_slug.get(slug)


lead = pick("les-100-meilleurs-albums-des-annees-2000-le-top-10") or arts[0]
alaune = [x for x in (pick(s) for s in ["lref-carte-de-marseille-par-jul", "lunatic-dans-la-legende",
                                          "booba-et-la-religion-oecumenisme-peches-et-paraboles",
                                          "dossier-sante-mentale-fin-silence-rap-francais"]) if x]
used = {lead["slug"], *[a["slug"] for a in alaune]}


def pick_sec(key, n):
    L = [a for a in by_sec[key] if a.get("image") and a["slug"] not in used and int(a["year"]) >= 2015][:n]
    used.update(a["slug"] for a in L)
    return L


ch, iv, ds, bi = pick_sec("chroniques", 4), pick_sec("interviews", 4), pick_sec("dossiers", 3), [a for a in by_sec["billets"] if a["slug"] not in used][:5]
ymax = max(years.values())
yrs = "".join(f'<a class="yr" href="articles.html?y={y}" style="--h:{years[y] / ymax:.3f}"><span class="yr-bar"></span><span class="yr-n">{years[y]}</span><span class="yr-y">{y}</span></a>' for y in sorted(years))
crew = "".join(f'<li><a href="articles.html?au={quote(n)}"><span class="crew-n">{esc(n)}</span><span class="crew-c">{c}</span></a></li>' for n, c in authors.most_common(24) if n != "La Rédaction")
ann = f'<a class="ann" href="top-100-annees-90.html"><span class="ann-k">Classement</span><span class="ann-t">Les 100 meilleurs albums des années 90</span><span class="ann-d">De Dee Nasty à L’école du micro d’argent, avec un texte pour chaque disque.</span></a>'


def sec_block(key, L, layout):
    label = SEC_LABEL[key]
    return f"""<section class="hsec hsec-{layout}"><header class="hsec-head"><h2><a href="rubrique/{key}.html">{esc(label)}</a></h2><a class="hsec-all" href="rubrique/{key}.html">Toutes les {esc(label.lower()) if key != 'billets' else 'billets'} ({num(len(by_sec[key]))})</a></header>
<div class="hsec-grid">{"".join(card(a, 0, "m") for a in L)}</div></section>"""


spines = "".join(f'<li class="k-{k}"><a href="rubrique/{k}.html"><span class="sp-n">{num(len(by_sec[k]))}</span><span class="sp-t">{esc(l.replace("Billets d'humeur", "Billets"))}</span></a></li>' for k, l, _, _ in SECTIONS)
body = f"""<section class="opening"><h1 class="opening-title">Le Rap<br>en France</h1><div class="opening-side"><p class="opening-sub"><span>{num(len(arts))} articles</span><span>{len(authors)} plumes</span><span>2011–2023</span></p><p class="opening-txt">Douze ans de chroniques, d'interviews et de dossiers sur le rap français, sauvés de l'oubli.</p></div></section>
<nav class="spines" aria-label="Rubriques"><ul>{spines}</ul></nav>
<section class="front">
 <article class="lead">
  <a class="lead-link" href="a/{lead['slug']}/">{thumb(lead, 0, "lead-img")}
  <span class="lead-over"><span class="kick k-{lead['sec']}">{esc(SEC_LABEL[lead['sec']])}</span>
  <span class="lead-title">{esc(lead['display'])}</span></span></a>
  <p class="lead-dek">{esc(lead['dek'])}</p>
  <p class="card-by">{byline(lead, False)}</p>
  <p class="lead-also"><a href="top-100-annees-2000.html">Voir les 100 albums du classement</a></p>
 </article>
 <aside class="alaune" aria-label="À la une">
  {ann}
  <ul class="rows">{"".join(row(a) for a in alaune)}</ul>
 </aside>
</section>
{sec_block("chroniques", ch, "four")}
{sec_block("interviews", iv, "four")}
<section class="hsec hsec-split">
 <div>{sec_block("dossiers", ds, "three")}</div>
 <div class="bil"><header class="hsec-head"><h2><a href="rubrique/billets.html">Billets d'humeur</a></h2></header><ul class="quotes">{"".join(f'<li><a href="a/{a["slug"]}/"><span class="q-t">{esc(a["display"])}</span><span class="q-m">{esc(a.get("author") or "")}{", " if a.get("author") else ""}{a["year"]}</span></a></li>' for a in bi)}</ul></div>
</section>
<section class="years"><header class="hsec-head"><h2>Douze ans de rap français</h2><p>Nombre d'articles archivés par année. Choisissez une année pour les parcourir.</p></header><div class="yrs">{yrs}</div></section>
<section class="crew"><header class="hsec-head"><h2>La rédaction</h2><p>{len(authors)} plumes ont écrit pour LREF. Voici les plus prolifiques.</p></header><ul class="crew-list">{crew}</ul></section>"""
write("index.html", page("Le Rap en France – archives 2011–2023", body, 0,
                         "Archives du média Le Rap en France (LREF) : chroniques, interviews, dossiers et classements, 2011–2023.", "home", img_url(lead.get("image", ""))))

body = f"""<article class="story"><header class="story-head"><h1>À propos de cette archive</h1></header><div class="prose">
<p>Le Rap en France (LREF) était un média web consacré au rap français, fondé en 2011 par Stéphane Fortems. Le site a réuni jusqu'à une trentaine de contributeurs bénévoles, publié un magazine papier bimestriel et atteint environ 1,5 million de pages vues.</p>
<p>Le site a été perdu à la suite d'un piratage et son nom de domaine a changé de mains. Cette archive rassemble les {num(len(arts))} articles dont la <a href="https://web.archive.org/">Wayback Machine</a> d'Internet Archive a conservé une copie, écrits par {len(authors)} auteurs.</p>
<p>Lors du piratage, une vingtaine d'articles avaient été remplacés par des publicités en anglais : la plupart ont été retrouvés dans des copies antérieures et réintégrés, les autres sont perdus. Les textes ont été relus automatiquement : typographie française, fautes d'orthographe et d'accord évidentes. Le style des auteurs, l'argot et les citations de paroles n'ont pas été modifiés.</p>
<p>Les brèves d'actualité (annonces de clips et de sorties, concours) n'ont pas été reprises, pas plus que les agendas de concerts et les annonces de festivals ou de soirées. Seuls les articles de fond et les revues hebdomadaires sont conservés.</p>
<p>Les images sont chargées depuis ces copies d'archive : celles qui n'ont jamais été archivées sont remplacées par un aplat de couleur. Chaque article renvoie vers sa copie d'origine.</p></div></article>"""
write("a-propos.html", page("À propos – Le Rap en France", body, 0))
write("404.html", page("Page introuvable – Le Rap en France",
      f'<article class="story"><header class="story-head"><h1>Cette page n\'existe pas dans l\'archive</h1><p class="standfirst">Elle n\'a peut-être jamais été conservée. <a href="{BASE}articles.html">Cherchez dans les {num(len(arts))} articles</a> ou revenez à <a href="{BASE}index.html">la une</a>.</p></header></article>'))

print("corrections :", dict(STATS), "· pages de spam écartées :", len(SPAM_RETIRES), "· brèves retirées :", len(BREVES))
print(f"{len(arts)} articles · rubriques {dict((k, len(v)) for k, v in by_sec.items())} · top90 {len(entries)} · top00 {len(rank00)}")
