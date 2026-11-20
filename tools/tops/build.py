#!/usr/bin/env python3
"""Génère les deux sites des Tops 100 LREF (années 90 et années 2000)."""
import json, re, html, shutil, unicodedata, sys
from pathlib import Path
from urllib.parse import quote_plus

ROOT = Path(__file__).parent
DATA = json.load(open(ROOT / "src" / "data.json"))
COVERS = json.load(open(ROOT / "src" / "covers.json")) if (ROOT / "src" / "covers.json").exists() else {}


def cover(site, e):
    return COVERS.get(("90" if site["theme"] == "k7" else "2000") + "-" + str(e["rank"]))


ONERR = "this.closest('figure').classList.add('nocover');this.remove()"
FONTS = ROOT / "fonts"

SITES = {
    "90": {
        "dir": "top100-annees-90",
        "title": "Les 100 meilleurs albums de rap français des années 90",
        "short": "Top 100 · années 90",
        "decade": "1990–1999",
        "theme": "k7",
        "faces": ("Face A", "Face B"),
        "other": ("2000", "Les années 2000", "https://2000.lref.fr/"),
        "intro": "Cent albums, de Dee Nasty à IAM, choisis par la rédaction du Rap en France et publiés en 2016. "
                 "Une décennie de cassettes copiées, de compilations, de maxis et de premiers albums qui ont fondé le rap français.",
        "method": [
            "Ce classement a été établi par la rédaction de Le Rap en France (LREF) et publié en dix tranches en 2016. "
            "Il couvre les albums, EP, mixtapes et compilations sortis entre 1990 et 1999.",
            "Les notices reprennent les textes d'origine, réécrits et augmentés en 2026 pour cette édition. "
            "Les années de sortie ne sont indiquées que lorsqu'elles sont sûres. "
            "Les faits ajoutés n'ont pas tous été revérifiés : signalez une erreur et elle sera corrigée.",
        ],
        "fonts": [("Archivo Black", "archivo-black-latin-400-normal.woff2", 400, "normal"),
                  ("Source Serif 4", "source-serif-4-latin-400-normal.woff2", 400, "normal"),
                  ("Source Serif 4", "source-serif-4-latin-400-italic.woff2", 400, "italic"),
                  ("Source Serif 4", "source-serif-4-latin-700-normal.woff2", 700, "normal")],
        "font_dirs": ["fontsource-archivo-black-5.3.0", "fontsource-source-serif-4-5.3.1"],
    },
    "2000": {
        "dir": "top100-annees-2000",
        "title": "Les 100 meilleurs albums de rap français des années 2000",
        "short": "Top 100 · années 2000",
        "decade": "2000–2009",
        "theme": "cd",
        "faces": ("Disque 1", "Disque 2"),
        "other": ("90", "Les années 90", "https://90.lref.fr/"),
        "intro": "Cent albums de Mauvais Œil à Secrets de l'oubli, élus par 43 critiques. "
                 "La décennie qu'on a trop vite enterrée : street CD, indépendance, Skyrock et 45 Scientific.",
        "method": [
            "Ce classement a été établi par 43 votants : la rédaction de Le Rap en France et celles de L'Abcdr du Son, "
            "Reaphit, Le Bon Son, Revrse et SURL, ainsi que Genono, Spleenter et Olivier Cachin. "
            "Chaque votant a classé 50 albums, de 50 points pour le premier à 1 point pour le cinquantième. "
            "Il a été publié sur LREF entre 2019 et 2022.",
            "Les notices reprennent les textes d'origine, réécrits et augmentés en 2026. "
            "Le top 10 a été vérifié ; pour les autres, les faits ajoutés n'ont pas tous été revérifiés. "
            "Pour les numéros 81 à 90, seul le morceau recommandé avait survécu dans les archives : leurs notices ont été réécrites.",
        ],
        "fonts": [("Unbounded", "unbounded-latin-700-normal.woff2", 700, "normal"),
                  ("Unbounded", "unbounded-latin-900-normal.woff2", 900, "normal"),
                  ("Manrope", "manrope-latin-400-normal.woff2", 400, "normal"),
                  ("Manrope", "manrope-latin-700-normal.woff2", 700, "normal")],
        "font_dirs": ["fontsource-unbounded-5.3.0", "fontsource-manrope-5.3.0"],
    },
}

ARCHIVE = "https://lref.fr/"


def slug(s):
    s = s.replace("Œ", "Oe").replace("œ", "oe").replace("Æ", "Ae").replace("æ", "ae")
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def inline(s):
    s = html.escape(s, quote=False)
    s = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"\*(.+?)\*", r"<em>\1</em>", s)
    s = re.sub(r"\\([\\*_\[\]()#.!-])", r"\1", s)
    return s


def plain(s):
    return re.sub(r"[*\\]", "", s)


def first_title(morceau):
    m = re.search(r"\*(.+?)\*", morceau)
    return plain(m.group(1)) if m else ""


def page(site, title, body, desc, depth=0, cls=""):
    up = "../" * depth
    other = site["other"]
    return f"""<!doctype html>
<html lang="fr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(desc)}">
<meta name="theme-color" content="{'#E9E8E3' if site['theme']=='k7' else '#0B1020'}">
<link rel="stylesheet" href="{up}style.css">
</head>
<body class="{site['theme']} {cls}">
<a class="skip" href="#main">Aller au contenu</a>
<header class="top">
  <a class="brand" href="{up}index.html"><span class="brand-lref">LREF</span> <span class="brand-t">{site['short']}</span></a>
  <nav aria-label="Navigation principale">
    <a href="{up}index.html#classement">Le classement</a>
    <a href="{up}index.html#methode">La méthode</a>
    <a href="{other[2]}">{other[1]}</a>
  </nav>
</header>
<main id="main">
{body}
</main>
<footer class="foot">
  <p>Un classement de <a href="{ARCHIVE}">Le Rap en France</a>, média fondé en 2011 par Stéphane Fortems.
  Les textes d'origine appartiennent à leurs auteurs, bénévoles de LREF.</p>
  <p><a href="{ARCHIVE}">Les archives LREF</a> · <a href="{other[2]}">{other[1]}</a></p>
</footer>
</body>
</html>
"""


def sleeve(site, e):
    a, al, r = html.escape(e["artist"]), inline(e["album"]), e["rank"]
    yr = e.get("year") or ""
    cv = cover(site, e)
    if site["theme"] == "k7":
        img = (f'<img class="jcard-img" src="{cv}" alt="" loading="eager" referrerpolicy="no-referrer" onerror="{ONERR}"><span class="jcard-sticker">{r}</span>' if cv else "")
        return f"""<figure class="jcard{' has-cover' if cv else ''}" aria-hidden="true">
  <div class="jcard-spine"><span>{a} — {al}</span></div>
  <div class="jcard-front">{img}
    <span class="jcard-n">{r}</span>
    <span class="jcard-a">{a}</span>
    <span class="jcard-t">{al}</span>
    <span class="jcard-y">{yr or 'Années 90'}</span>
    <span class="jcard-tape"></span>
  </div>
</figure>"""
    img = f'<img class="cd-cover" src="{cv}" alt="" referrerpolicy="no-referrer" onerror="{ONERR}">' if cv else ""
    return f"""<figure class="disc-wrap{' has-cover' if cv else ''}" aria-hidden="true">{img}
  <div class="disc">
    <div class="disc-label">
      <span class="disc-n">{r:02d}</span>
      <span class="disc-a">{a}</span>
      <span class="disc-t">{al}</span>
      <span class="disc-y">{yr}</span>
    </div>
  </div>
</figure>"""


def album_page(site, items, i):
    e = items[i]
    r = e["rank"]
    up_e = next((x for x in items if x["rank"] == r + 1), None)
    dn_e = next((x for x in items if x["rank"] == r - 1), None)
    paras = e["paras"]
    chapo = e.get("chapo")
    body_paras = "\n".join(
        f'<p class="{"lede" if k == 0 else ""}">{inline(p)}</p>' for k, p in enumerate(paras))
    pourquoi = (f'<section class="pourquoi"><h2>Pourquoi cet album ?</h2><p>{inline(e["pourquoi"])}</p></section>'
                if e.get("pourquoi") else "")
    track = first_title(e["morceau"])
    q = quote_plus(f"{plain(e['artist'])} {track}")
    rewritten = (site["theme"] == "cd" and 81 <= r <= 90)
    note = ('<p class="note">Seule la recommandation d\'origine a survécu pour ce numéro : '
            'la notice a été réécrite en 2026 et reste à relire.</p>') if rewritten else ""
    nav = '<nav class="pager" aria-label="Albums voisins">'
    nav += (f'<a class="prev" href="{fname(up_e)}"><small>N° {up_e["rank"]}</small>{html.escape(up_e["artist"])}</a>'
            if up_e else '<span></span>')
    nav += '<a class="all" href="../index.html#classement">Tout le classement</a>'
    nav += (f'<a class="next" href="{fname(dn_e)}"><small>N° {dn_e["rank"]}</small>{html.escape(dn_e["artist"])}</a>'
            if dn_e else '<span></span>')
    nav += "</nav>"
    body = f"""<article class="album">
  <div class="album-head">
    {sleeve(site, e)}
    <div class="album-id">
      <p class="album-rank">N° {r} <span>sur 100</span></p>
      <h1><span class="h-artist">{html.escape(e['artist'])}</span> <span class="h-album">{inline(e['album'])}</span></h1>
      {f'<p class="chapo">{inline(chapo)}</p>' if chapo else ''}
      {f'<p class="fiche">{inline(e["fiche"])}</p>' if e.get('fiche') else ''}
    </div>
  </div>
  <div class="album-body">
    {body_paras}
    {pourquoi}
    <section class="ecoute">
      <h2>Le morceau à écouter</h2>
      <p>{inline(e['morceau'])}</p>
      <p class="ecoute-links"><a href="https://www.youtube.com/results?search_query={q}" rel="noopener">Chercher sur YouTube</a>
      <a href="https://open.spotify.com/search/{quote_plus(plain(e['artist']) + ' ' + track).replace('+', '%20')}" rel="noopener">Chercher sur Spotify</a></p>
    </section>
    {note}
  </div>
  {nav}
</article>"""
    t = f"N° {r} · {plain(e['artist'])} – {plain(e['album'])} · {site['short']}"
    desc = plain(paras[0])[:180] if paras else site["intro"]
    return page(site, t, body, desc, depth=1)


def fname(e):
    return f"{e['rank']:03d}-{slug(e['artist'] + '-' + e['album'])}.html"


def index_page(site, items):
    def row(e):
        cv = cover(site, e)
        th = (f'<img class="th" src="{cv}" alt="" loading="lazy" referrerpolicy="no-referrer" onerror="this.style.visibility=\'hidden\'">' if cv else '<span class="th"></span>')
        return (f'<li><a href="a/{fname(e)}">{th}<span class="r">{e["rank"]}</span>'
                f'<span class="ar">{html.escape(e["artist"])}</span>'
                f'<span class="al">{inline(e["album"])}</span>'
                f'<span class="y">{e.get("year") or ""}</span></a></li>')
    desc_items = sorted(items, key=lambda x: -x["rank"])
    side1 = [e for e in desc_items if e["rank"] > 50]
    side2 = [e for e in desc_items if e["rank"] <= 50]
    top = sorted(items, key=lambda x: x["rank"])[:3]
    if site["theme"] == "k7":
        hero = f"""<section class="hero">
  <p class="hero-kicker">Le Rap en France présente</p>
  <h1 class="hero-title"><span class="big">100</span><span class="t">albums de rap français<br>des années 90</span></h1>
  <p class="hero-intro">{site['intro']}</p>
  <p class="hero-cta"><a href="a/{fname(desc_items[0])}">Commencer au n° 100</a> <a class="ghost" href="a/{fname(top[0])}">Aller au n° 1</a></p>
</section>"""
    else:
        hero = f"""<section class="hero">
  <div class="hero-disc" aria-hidden="true"><div class="disc spin"><div class="disc-label"><span class="disc-n">100</span><span class="disc-a">albums</span><span class="disc-t">2000–2009</span></div></div></div>
  <div class="hero-txt">
    <p class="hero-kicker">Le Rap en France présente</p>
    <h1 class="hero-title">Les 100 meilleurs albums de rap français des années 2000</h1>
    <p class="hero-intro">{site['intro']}</p>
    <p class="hero-cta"><a href="a/{fname(desc_items[0])}">Commencer au n° 100</a> <a class="ghost" href="a/{fname(top[0])}">Aller au n° 1</a></p>
  </div>
</section>"""
    podium = "".join(
        f'<li><a href="a/{fname(e)}"><span class="pr">{e["rank"]}</span><span class="pa">{html.escape(e["artist"])}</span>'
        f'<span class="pt">{inline(e["album"])}</span></a></li>' for e in top)
    body = f"""{hero}
<section class="podium" aria-labelledby="podium-h">
  <h2 id="podium-h">Le podium</h2>
  <ol>{podium}</ol>
</section>
<section id="classement" class="tracklist" aria-labelledby="cl-h">
  <div class="tl-head">
    <h2 id="cl-h">Le classement</h2>
    <label class="filter"><span>Chercher un artiste ou un album</span>
      <input id="q" type="search" placeholder="Booba, Oxmo, Assassin…" autocomplete="off"></label>
  </div>
  <div class="sides">
    <div class="side"><h3>{site['faces'][0]} <small>100 → 51</small></h3><ol>{''.join(row(e) for e in side1)}</ol></div>
    <div class="side"><h3>{site['faces'][1]} <small>50 → 1</small></h3><ol>{''.join(row(e) for e in side2)}</ol></div>
  </div>
  <p id="nores" class="nores" hidden>Aucun album ne correspond. Essayez un autre nom.</p>
</section>
<section id="methode" class="methode" aria-labelledby="m-h">
  <h2 id="m-h">La méthode</h2>
  {''.join(f'<p>{p}</p>' for p in site['method'])}
</section>
<script>
(function(){{var q=document.getElementById('q'),rows=[].slice.call(document.querySelectorAll('.side li')),nr=document.getElementById('nores');
function n(s){{return s.normalize('NFD').replace(/[\\u0300-\\u036f]/g,'').toLowerCase();}}
q.addEventListener('input',function(){{var v=n(q.value.trim()),c=0;rows.forEach(function(li){{var ok=!v||n(li.textContent).indexOf(v)>-1;li.hidden=!ok;if(ok)c++;}});nr.hidden=c>0;}});}})();
</script>"""
    return page(site, site["title"] + " · LREF", body, site["intro"], cls="home")


def build(key):
    site = SITES[key]
    out = ROOT / "out" / site["dir"]
    if out.exists():
        for p in out.iterdir():
            if p.name in (".git", "CNAME"):
                continue
            shutil.rmtree(p) if p.is_dir() else p.unlink()
    (out / "a").mkdir(parents=True, exist_ok=True)
    (out / "fonts").mkdir(exist_ok=True)
    css = ""
    for fam, f, w, st in site["fonts"]:
        for d in site["font_dirs"]:
            src = FONTS / d / "files" / f
            if src.exists():
                shutil.copy(src, out / "fonts" / f)
        css += f"@font-face{{font-family:'{fam}';src:url(fonts/{f}) format('woff2');font-weight:{w};font-style:{st};font-display:swap}}\n"
    css += (ROOT / f"{site['theme']}.css").read_text()
    (out / "style.css").write_text(css)
    items = DATA[key]
    for i, e in enumerate(items):
        (out / "a" / fname(e)).write_text(album_page(site, items, i))
    (out / "index.html").write_text(index_page(site, items))
    (out / "404.html").write_text(page(site, "Page introuvable", f'<section class="methode"><h1>Page introuvable</h1><p>Cette page n\'existe pas. <a href="/{site["dir"]}/index.html">Retour au classement</a>.</p></section>', site["intro"]))
    (out / ".nojekyll").write_text("")
    (out / "README.md").write_text(f"# {site['title']}\n\nSite statique généré depuis l'archive de Le Rap en France.\n")
    print(key, "→", out, len(items), "albums")


if __name__ == "__main__":
    for k in (sys.argv[1:] or ["90", "2000"]):
        build(k)
