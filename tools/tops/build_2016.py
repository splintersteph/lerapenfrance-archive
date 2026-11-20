#!/usr/bin/env python3
"""Site « Une année 2016 » : les 116 morceaux préférés de LREF en 2016."""
import json, re, html, shutil, os, sys
from pathlib import Path
from urllib.parse import quote_plus

ROOT = Path(__file__).parent
ARCH_REPO = Path("/home/claude/lerapenfrance-archive")
DATA = json.load(open(ARCH_REPO / "data" / "top-morceaux-2016.json"))
OUT = ROOT / "out" / "top-morceaux-2016"
ARCHIVE = "https://lref.fr/"
ARCH_SLUGS = set(os.listdir(ARCH_REPO / "a")) if (ARCH_REPO / "a").exists() else set()
FONTS = ROOT / "fonts"
FONT_FILES = [("Syne", "fontsource-syne-5.3.0", "syne-latin-800-normal.woff2", 800, "normal"),
              ("Syne", "fontsource-syne-5.3.0", "syne-latin-700-normal.woff2", 700, "normal"),
              ("Work Sans", None, "work-sans-latin-400-normal.woff2", 400, "normal"),
              ("Work Sans", None, "work-sans-latin-400-italic.woff2", 400, "italic"),
              ("Work Sans", None, "work-sans-latin-600-normal.woff2", 600, "normal")]

FIX = {  # casse lisible pour quelques noms
    "PNL": "PNL", "SCH": "SCH", "MHD": "MHD", "A2H": "A2H", "JUL": "Jul", "MZ": "MZ", "KT": "KT", "JP": "JP",
    "TSR": "TSR", "S-CREW": "S-Crew", "X": "x", "&": "&", "SPRI": "S.Pri", "D'EN": "d'en",
}
SMALL = {"de", "du", "des", "la", "le", "les", "et", "à", "au", "en", "d’", "l’", "un", "une", "pas", "sur"}


def nice(s):
    s = s.strip()
    if not s.isupper():
        return s
    out = []
    for i, w in enumerate(s.split()):
        if w in FIX:
            out.append(FIX[w]); continue
        lw = w.lower()
        if i and lw in SMALL:
            out.append(lw); continue
        # garde les apostrophes : J’AURAIS -> J’aurais
        out.append(lw[:1].upper() + lw[1:])
    return " ".join(out)


def yt_id(u):
    m = re.search(r"[?&]v=([\w-]{11})", u or "")
    return m.group(1) if m else ""


def esc(s):
    return html.escape(s, quote=True)


def chron_link(u):
    if not u:
        return ""
    slug = u.rstrip("/").split("/")[-1]
    if slug in ARCH_SLUGS:
        return ARCHIVE + "a/" + slug + "/"
    return "https://web.archive.org/web/2018/" + u


def thumb(e):
    vid = yt_id(e["youtube"])
    ytt = f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg" if vid else ""
    src = ("https://web.archive.org/web/2017im_/" + e["img"]) if e["img"] else ytt
    if not src:
        return '<span class="art art-empty" aria-hidden="true"></span>'
    fb = (f"if(this.dataset.f!=='1'&&'{ytt}'){{this.dataset.f='1';this.src='{ytt}'}}else{{this.parentNode.classList.add('art-empty');this.remove()}}")
    return f'<span class="art"><img src="{esc(src)}" alt="" loading="lazy" referrerpolicy="no-referrer" onerror="{fb}"></span>'


def listen(e):
    vid = yt_id(e["youtube"])
    a, t = nice(e["artist"]), nice(e["title"])
    if vid:
        return f'<a class="play" href="https://www.youtube.com/watch?v={vid}" rel="noopener">Écouter</a>'
    return f'<a class="play" href="https://www.youtube.com/results?search_query={quote_plus(a + " " + t)}" rel="noopener">Chercher sur YouTube</a>'


def img_url(e):
    vid = yt_id(e["youtube"])
    if e["img"]:
        return "https://web.archive.org/web/2017im_/" + e["img"]
    if e.get("cover"):
        return e["cover"]
    return f"https://i.ytimg.com/vi/{vid}/hqdefault.jpg" if vid else ""


def listen_url(e):
    vid = yt_id(e["youtube"])
    if vid:
        return f"https://www.youtube.com/watch?v={vid}", "Écouter"
    return "https://www.youtube.com/results?search_query=" + quote_plus(nice(e["artist"]) + " " + nice(e["title"])), "Chercher sur YouTube"


def item(e, big=False):
    a, t = e["artist"].strip(), e["title"].strip()
    ch = chron_link(e["chronique"])
    u = img_url(e)
    lu, ll = listen_url(e)
    chl = f'<a class="more" href="{esc(ch)}">Lire l\'article</a>' if ch else ""
    bg = f' style="--img:url(\'{esc(u)}\')"' if u else ""
    art = (f'<img src="{esc(u)}" alt="" loading="lazy" referrerpolicy="no-referrer" onerror="this.remove()">' if u else "")
    return f"""<li class="trk{' big' if big else ''}" id="n{e['rank']}" data-rk="{e['rank']}" data-ar="{esc(a)}" data-ti="{esc(t)}" data-u="{esc(lu)}"{bg}>
  <div class="trk-bg" aria-hidden="true"></div>
  <span class="rk" aria-hidden="true">{e['rank']}</span>
  <div class="sleeve">{art}<span class="sleeve-n">N° {e['rank']}</span></div>
  <div class="tx">
    <h3><span class="sr">N° {e['rank']} : </span><span class="ar">{esc(a)}</span> <span class="ti">{esc(t)}</span></h3>
    <p>{esc(e['text'])}</p>
    <p class="act"><a class="play" href="{esc(lu)}" rel="noopener">{ll}</a>{chl}</p>
  </div>
</li>"""


def build():
    if OUT.exists():
        for p in OUT.iterdir():
            if p.name in (".git", "CNAME"):
                continue
            shutil.rmtree(p) if p.is_dir() else p.unlink()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "fonts").mkdir(exist_ok=True)
    css = ""
    for fam, d, f, w, st in FONT_FILES:
        src = next(FONTS.glob(f"*/files/{f}"))
        shutil.copy(src, OUT / "fonts" / f)
        css += f"@font-face{{font-family:'{fam}';src:url(fonts/{f}) format('woff2');font-weight:{w};font-style:{st};font-display:swap}}\n"
    css += (ROOT / "m2016.css").read_text()
    (OUT / "style.css").write_text(css)

    items = sorted(DATA, key=lambda e: -e["rank"])
    top10 = sorted([e for e in DATA if e["rank"] <= 10], key=lambda e: e["rank"])
    wall = "".join(f'<img src="{esc(img_url(e))}" alt="" loading="lazy" referrerpolicy="no-referrer" onerror="this.style.visibility=\'hidden\'">' for e in items if e["img"])
    tens = []
    for start in range(116, 10, -10):
        end = max(start - 9, 11)
        grp = [e for e in items if end <= e["rank"] <= start]
        tens.append(f'<section class="tens" aria-label="Numéros {start} à {end}"><h3 class="tens-h"><span>{start}</span><i></i><span>{end}</span></h3><ol>{"".join(item(e) for e in grp)}</ol></section>')
    body = f"""<div class="nowbar" id="nowbar" aria-live="polite" hidden>
  <span class="nb-eq" aria-hidden="true"><i></i><i></i><i></i><i></i></span>
  <span class="nb-lbl">En lecture</span>
  <a class="nb-t" id="nbt" href="#">—</a>
  <span class="nb-prog" aria-hidden="true"><span id="nbp"></span></span>
</div>
<header class="top">
  <a class="brand" href="index.html"><b>LREF</b> Une année 2016</a>
  <nav><a href="#liste">Le compte à rebours</a><a href="#top10">Le top 10</a><a href="{ARCHIVE}">Les archives</a></nav>
</header>
<main id="main">
<section class="hero">
  <div class="wall" aria-hidden="true">{wall}</div>
  <div class="hero-tx">
    <p class="kick">Le Rap en France · sélection de la rédaction</p>
    <h1><span class="h-n">116</span><span class="h-w">morceaux de rap français</span><span class="h-y">2016</span></h1>
    <p class="intro">Une année si riche qu'il aurait été dommage de n'en garder que dix sons. En janvier 2017, la rédaction en avait retenu 116, pour se souvenir de 2016 dans cinq, dix ou vingt ans. Les voici, restaurés depuis le mini-site d'origine.</p>
    <p class="cta"><a href="#n116">Lancer le compte à rebours</a><a class="ghost" href="#top10">Aller au top 10</a></p>
  </div>
</section>
<section id="liste" class="liste" aria-labelledby="lh">
  <div class="lhead"><h2 id="lh">Le compte à rebours <small>116 → 11</small></h2>
  <label class="filter"><span>Chercher un artiste ou un titre</span><input id="q" type="search" placeholder="PNL, Damso, Lomepal…" autocomplete="off"></label></div>
  {"".join(tens)}
  <p id="nores" class="nores" hidden>Aucun morceau ne correspond.</p>
</section>
<section id="top10" class="top10" aria-labelledby="t10h">
  <h2 id="t10h"><span>Le top</span> <span class="ten">10</span></h2>
  <ol>{"".join(item(e, big=True) for e in sorted(top10, key=lambda e: -e["rank"]))}</ol>
</section>
<section class="note">
  <p>Textes de la rédaction de Le Rap en France, publiés en janvier 2017 sur <em>uneannee2016.lerapenfrance.fr</em> et restaurés depuis la Wayback Machine.
  Les vidéos du top 10 n'ont pas été archivées : les boutons lancent une recherche YouTube.</p>
</section>
</main>
<footer class="foot"><p>Un classement de <a href="{ARCHIVE}">Le Rap en France</a> · Les tops albums des <a href="https://90.lref.fr/">années 90</a> et des <a href="https://2000.lref.fr/">années 2000</a>.</p></footer>
<script>
(function(){{
var q=document.getElementById('q'),rows=[].slice.call(document.querySelectorAll('#liste .trk')),secs=[].slice.call(document.querySelectorAll('.tens')),nr=document.getElementById('nores');
function n(s){{return s.normalize('NFD').replace(/[\\u0300-\\u036f]/g,'').toLowerCase();}}
q.addEventListener('input',function(){{var v=n(q.value.trim()),c=0;rows.forEach(function(li){{var ok=!v||n(li.dataset.ar+' '+li.dataset.ti).indexOf(v)>-1;li.hidden=!ok;if(ok)c++;}});
secs.forEach(function(s){{s.hidden=!s.querySelector('.trk:not([hidden])');}});nr.hidden=c>0;}});
var bar=document.getElementById('nowbar'),t=document.getElementById('nbt'),p=document.getElementById('nbp');
var all=[].slice.call(document.querySelectorAll('.trk'));
if('IntersectionObserver' in window){{var io=new IntersectionObserver(function(es){{es.forEach(function(e){{if(e.isIntersecting){{var li=e.target;all.forEach(function(x){{x.classList.toggle('on',x===li);}});
bar.hidden=false;t.textContent='N° '+li.dataset.rk+' · '+li.dataset.ar+' — '+li.dataset.ti;t.href=li.dataset.u;p.style.width=((117-li.dataset.rk)/116*100)+'%';}}}});}},{{rootMargin:'-45% 0px -50% 0px'}});
all.forEach(function(li){{io.observe(li);}});}}
}})();
</script>"""
    page = f"""<!doctype html>
<html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Une année 2016 · 116 morceaux de rap français · LREF</title>
<meta name="description" content="Les 116 morceaux de rap français préférés de la rédaction de Le Rap en France en 2016, de Columbine à Hugo TSR.">
<meta name="theme-color" content="#0C0920">
<link rel="stylesheet" href="style.css"></head>
<body><a class="skip" href="#main">Aller au contenu</a>
{body}
</body></html>"""
    (OUT / "index.html").write_text(page)
    (OUT / ".nojekyll").write_text("")
    (OUT / "README.md").write_text("# Une année 2016 — 116 morceaux de rap français (LREF)\n")
    print("ok", len(items))


if __name__ == "__main__":
    build()
