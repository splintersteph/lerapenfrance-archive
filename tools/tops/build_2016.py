#!/usr/bin/env python3
"""Site « Une année 2016 » : les 116 morceaux préférés de LREF en 2016."""
import json, re, html, shutil, os, sys
from pathlib import Path
from urllib.parse import quote_plus

ROOT = Path(__file__).parent
ARCH_REPO = Path("/home/claude/lerapenfrance-archive")
DATA = json.load(open(ARCH_REPO / "data" / "top-morceaux-2016.json"))
OUT = ROOT / "out" / "top-morceaux-2016"
ARCHIVE = "https://splintersteph.github.io/lerapenfrance-archive/"
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


def item(e, big=False):
    a, t = e["artist"].strip(), e["title"].strip()
    ch = chron_link(e["chronique"])
    chl = f'<a class="more" href="{esc(ch)}">L\'article sur LREF</a>' if ch else ""
    return f"""<li class="trk{' big' if big else ''}" id="n{e['rank']}">
  <span class="rk">{e['rank']}</span>
  {thumb(e)}
  <div class="tx">
    <h3><span class="ar">{esc(a)}</span> <span class="ti">{esc(t)}</span></h3>
    <p>{esc(e['text'])}</p>
    <p class="act">{listen(e)}{chl}</p>
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
    mosaic_src = [e for e in items if e["img"]][:16]
    mosaic = "".join(f'<img src="https://web.archive.org/web/2017im_/{esc(e["img"])}" alt="" referrerpolicy="no-referrer" onerror="this.style.visibility=\'hidden\'">' for e in mosaic_src)
    tens = []
    for start in range(116, 0, -10):
        end = max(start - 9, 1)
        grp = [e for e in items if end <= e["rank"] <= start]
        tens.append(f'<section class="tens" aria-label="Numéros {start} à {end}"><h3 class="tens-h">{start}–{end}</h3><ol>{"".join(item(e) for e in grp)}</ol></section>')
    body = f"""<header class="top">
  <a class="brand" href="index.html"><b>LREF</b> Une année 2016</a>
  <nav><a href="#top10">Le top 10</a><a href="#liste">Les 116</a><a href="{ARCHIVE}">Les archives LREF</a></nav>
</header>
<main id="main">
<section class="hero">
  <div class="mosaic" aria-hidden="true">{mosaic}</div>
  <div class="hero-tx">
    <p class="kick">Le Rap en France · janvier 2017</p>
    <h1><span>116 morceaux</span> de rap français en <em>2016</em></h1>
    <p class="intro">Cette année de rap français a été si riche qu'il aurait été dommage de n'en garder que dix sons.
    La rédaction en avait choisi 116, pas seulement pour les classer, mais pour se souvenir de cette année dans 5, 10 ou 20 ans.
    Les voici, restaurés depuis les archives du mini-site <em>uneannee2016.lerapenfrance.fr</em>.</p>
    <p class="cta"><a href="#n116">Lancer le compte à rebours</a><a class="ghost" href="#top10">Aller au top 10</a></p>
  </div>
</section>
<section id="top10" class="top10" aria-labelledby="t10h">
  <h2 id="t10h">Le top 10</h2>
  <ol>{"".join(item(e, big=True) for e in top10)}</ol>
</section>
<section id="liste" class="liste" aria-labelledby="lh">
  <div class="lhead"><h2 id="lh">Les 116, de 116 à 1</h2>
  <label class="filter"><span>Chercher un artiste ou un titre</span><input id="q" type="search" placeholder="PNL, Damso, Lomepal…" autocomplete="off"></label></div>
  {"".join(tens)}
  <p id="nores" class="nores" hidden>Aucun morceau ne correspond.</p>
</section>
<section class="note">
  <p>Textes de la rédaction de Le Rap en France, publiés en janvier 2017. Les visuels proviennent du mini-site d'origine, conservé par la Wayback Machine ;
  quand ils manquent, la vignette YouTube prend le relais. Pour le top 10, les vidéos n'ont pas été archivées : les boutons lancent une recherche YouTube.</p>
</section>
</main>
<footer class="foot"><p>Un classement de <a href="{ARCHIVE}">Le Rap en France</a> · Voir aussi les tops albums des <a href="https://splintersteph.github.io/top100-annees-90/">années 90</a> et des <a href="https://splintersteph.github.io/top100-annees-2000/">années 2000</a>.</p></footer>
<script>
(function(){{var q=document.getElementById('q'),rows=[].slice.call(document.querySelectorAll('#liste .trk')),secs=[].slice.call(document.querySelectorAll('.tens')),nr=document.getElementById('nores');
function n(s){{return s.normalize('NFD').replace(/[\\u0300-\\u036f]/g,'').toLowerCase();}}
q.addEventListener('input',function(){{var v=n(q.value.trim()),c=0;rows.forEach(function(li){{var ok=!v||n(li.querySelector('h3').textContent).indexOf(v)>-1;li.hidden=!ok;if(ok)c++;}});
secs.forEach(function(s){{s.hidden=!s.querySelector('.trk:not([hidden])');}});nr.hidden=c>0;}});}})();
</script>"""
    page = f"""<!doctype html>
<html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>Une année 2016 · 116 morceaux de rap français · LREF</title>
<meta name="description" content="Les 116 morceaux de rap français préférés de la rédaction de Le Rap en France en 2016, de Columbine à Hugo TSR.">
<meta name="theme-color" content="#EDEBFF">
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
