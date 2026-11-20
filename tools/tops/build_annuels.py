#!/usr/bin/env python3
"""Génère albums.lref.fr : les tops albums annuels de LREF (2013–2022)."""
import json, html, os, re, shutil, unicodedata, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out", "albums-annuels")
DATA = json.load(open(os.path.join(HERE, "annuels", "years.json")))
ARCHIVE = "https://lref.fr/"
FONTS = "/tmp/fz"

YEARS = {
    "2013":    dict(label="2013", color="#FF5A36", kind="albums", short="2013"),
    "2014":    dict(label="2014", color="#FFD23F", kind="albums", short="2014"),
    "2014-ep": dict(label="2014", color="#9BE564", kind="EPs & mixtapes", short="EPs 2014"),
    "2015":    dict(label="2015", color="#FF8FB1", kind="projets", short="2015"),
    "2016":    dict(label="2016", color="#7CE0FF", kind="projets", short="2016"),
    "2017":    dict(label="2017", color="#5577FF", kind="projets", short="2017"),
    "2018":    dict(label="2018", color="#FF7AC6", kind="projets", short="2018"),
    "2020":    dict(label="2020", color="#B9A2FF", kind="projets", short="2020"),
    "2021":    dict(label="2021", color="#2FD1BF", kind="projets", short="2021"),
    "2022":    dict(label="2022", color="#FFA024", kind="projets", short="2022"),
}
NOTES = {
    "2013": "Le bilan 2013 n'était pas classé : dix albums, présentés dans l'ordre de l'article d'origine.",
    "2015": "En 2015, la rédaction avait décidé de ne plus classer de 1 à 10 : dix projets, présentés dans l'ordre de l'article d'origine.",
    "2022": "L'article d'origine annonçait 15 projets mais passe directement du n° 15 au n° 13 : il n'y a jamais eu de n° 14.",
}
ORDER = list(YEARS)


def esc(s):
    return html.escape(s, quote=True)


def plain(s):
    return re.sub(r"<[^>]+>", "", s)


def slug(s):
    s = s.replace("Œ", "Oe").replace("œ", "oe")
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def keep(p):
    t = plain(p).strip()
    return t and t not in ("(ICI)", "ICI") and not t.startswith("Sujets")


def para(p):
    q = p.startswith("> ")
    m = re.fullmatch(r"\s*<strong>(.*)</strong>\s*", p, re.S)
    if m and "<strong>" not in m.group(1):
        p = m.group(1)
    bold = sum(len(plain(s)) for s in re.findall(r"<strong>(.*?)</strong>", p, re.S))
    if bold > 0.7 * max(1, len(plain(p))):
        p = re.sub(r"</?strong>", "", p)
    p = p[2:] if q else p
    # le texte vient déjà de l'archive, avec seulement <strong>/<em>
    p = re.sub(r"<(?!/?(strong|em)>)[^>]*>", "", p)
    return f"<blockquote><p>{p}</p></blockquote>" if q else f"<p>{p}</p>"


def page(title, desc, body, color, cls=""):
    return f"""<!doctype html>
<html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="theme-color" content="{color}">
<link rel="stylesheet" href="/style.css?v=4">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Ccircle cx='32' cy='32' r='30' fill='%23141414'/%3E%3Ccircle cx='32' cy='32' r='9' fill='{urllib.parse.quote(color)}'/%3E%3C/svg%3E">
</head><body class="{cls}" style="--c:{color}">
{body}
</body></html>
"""


def top_bar():
    return ('<header class="bar"><a class="home" href="/">Les albums de l\'année</a>'
            '<nav aria-label="Années">' +
            "".join(f'<a href="/{k}/" style="--c:{v["color"]}">{esc(v["short"])}</a>' for k, v in YEARS.items()) +
            '</nav></header>')


def footer():
    return ('<footer class="foot"><p>Classements de la rédaction de <a href="https://lref.fr/">Le Rap en France</a>, '
            'restaurés depuis la Wayback Machine. Pochettes : archives LREF, Deezer, Cover Art Archive.</p>'
            '<p>Voir aussi : les tops albums des <a href="https://90.lref.fr/">années 90</a> et des '
            '<a href="https://2000.lref.fr/">années 2000</a>, et <a href="https://2016.lref.fr/">Une année 2016</a> en 116 morceaux.</p></footer>')


def winner(m):
    its = m["items"]
    if its[0]["rank"] is None:
        return its[0]
    return min(its, key=lambda x: x["rank"])


def card(m, x, i):
    y = YEARS[m["key"]]
    q = f'{plain(x["artist"])} {plain(x["album"])}'
    rk = f'{x["rank"]}' if x["rank"] is not None else f'{i + 1:02d}'
    lab = "N°" if x["rank"] is not None else "Sélection"
    first = x["rank"] == 1
    paras = "".join(para(p) for p in x["paras"] if keep(p))
    return f"""<li class="al{' one' if first else ''}" id="n{rk}">
  <div class="sleeve">
    <span class="ph" aria-hidden="true">{esc(x['album'])}</span>
    <img src="{esc(x['img'])}" alt="Pochette de {esc(plain(x['album']))}, {esc(plain(x['artist']))}" loading="lazy" onerror="this.remove()">
    <span class="rk" aria-hidden="true">{rk}</span>
  </div>
  <div class="tx">
    <p class="pos">{lab} {rk}{' · ' + y['label'] if first else ''}</p>
    <h2><span class="ar">{esc(x['artist'])}</span> <span class="ti">{esc(x['album'])}</span></h2>
    {paras}
    <p class="ls"><a href="https://open.spotify.com/search/{urllib.parse.quote(q)}">Spotify</a>
    <a href="https://www.deezer.com/search/{urllib.parse.quote(q)}/album">Deezer</a>
    <a href="https://www.youtube.com/results?search_query={urllib.parse.quote_plus(q)}">YouTube</a></p>
  </div>
</li>"""


def year_page(m):
    k = m["key"]
    y = YEARS[k]
    items = m["items"]
    w = winner(m)
    idx = ORDER.index(k)
    prv = DATA[idx - 1] if idx > 0 else None
    nxt = DATA[idx + 1] if idx + 1 < len(DATA) else None

    def nav_link(o, cls):
        if not o:
            return "<span></span>"
        oy = YEARS[o["key"]]
        ow = winner(o)
        lead = "N° 1" if o["items"][0]["rank"] is not None else "En tête"
        return (f'<a class="{cls}" href="/{o["key"]}/" style="--c:{oy["color"]}"><small>{esc(oy["short"])} · {oy["kind"]}</small>'
                f'<b>{esc(ow["artist"])}</b><em>{lead} : {esc(ow["album"])} · {oy["label"]}</em></a>')

    intro = "".join(para(p) for p in m["intro"])
    note = f'<p class="note">{esc(NOTES[k])}</p>' if k in NOTES else ""
    covers = "".join(f'<img src="{esc(x["img"])}" alt="" loading="lazy" onerror="this.remove()">' for x in items)
    head = "La sélection" if items[0]["rank"] is None else f"Le top {len(items) + (1 if k == '2022' else 0)}"
    body = f"""{top_bar()}
<main>
<section class="yhero">
  <div class="ywrap">
    <p class="kind">Les meilleurs {esc(y['kind'])} de</p>
    <h1>{y['label']}</h1>
    <div class="stack" aria-hidden="true">{covers}</div>
  </div>
  <div class="lede">
    <p class="by">{esc(m['title'])} · par {esc(m['author'])}, le {esc(m['date'])} · <a href="{ARCHIVE}a/{m['slug']}/">article d'origine</a></p>
    {intro}
    {note}
  </div>
</section>
<h2 class="sec">{head}</h2>
<ol class="list">
{''.join(card(m, x, i) for i, x in enumerate(items))}
</ol>
<nav class="pager" aria-label="Autres années">{nav_link(prv, 'prev')}<a class="all" href="/">Toutes les années</a>{nav_link(nxt, 'next')}</nav>
</main>
{footer()}"""
    t = f"Les meilleurs {y['kind']} de {y['label']} · LREF"
    d = f"Le classement des meilleurs {y['kind']} de rap français de {y['label']} par la rédaction de Le Rap en France."
    return page(t, d, body, y["color"], "year")


def index_page():
    spines = []
    for m in DATA:
        k = m["key"]
        y = YEARS[k]
        w = winner(m)
        lead = "N° 1" if m["items"][0]["rank"] is not None else "En tête"
        spines.append(f"""<li style="--c:{y['color']}"><a href="/{k}/">
  <span class="yr">{"EPs 14" if k=="2014-ep" else y['label']}</span>
  <span class="cv"><span class="ph">{esc(w['album'])}</span><img src="{esc(w['img'])}" alt="" loading="lazy" onerror="this.remove()"></span>
  <span class="meta"><small>{esc(y['kind'])} · {len(m['items'])} titres</small><b>{esc(w['artist'])}</b><em>{lead} : {esc(w['album'])}</em></span>
</a></li>""")
    body = f"""{top_bar()}
<main>
<section class="hub">
  <h1>Les albums<br>de l'année</h1>
  <p>Chaque hiver, la rédaction de <a href="https://lref.fr/">Le Rap en France</a> se disputait pendant des semaines pour garder dix disques. Voici ce qu'il reste de ces bilans, de 2013 à 2022 : {sum(len(m['items']) for m in DATA)} projets, leurs pochettes et les textes d'époque.</p>
</section>
<ol class="spines">
{''.join(spines)}
</ol>
<p class="gap">Le bilan 2019 n'a pas été retrouvé dans les archives.</p>
</main>
{footer()}"""
    return page("Les albums de l'année · Le Rap en France 2013–2022",
                "Les tops albums annuels de la rédaction de Le Rap en France, de 2013 à 2022.",
                body, "#141414", "hub-page")


def build():
    if os.path.exists(OUT):
        shutil.rmtree(OUT)
    os.makedirs(os.path.join(OUT, "fonts"))
    for pkg, fam, ws in [("fontsource-big-shoulders-display-5", "big-shoulders-display", ["800-normal", "900-normal"]),
                         ("fontsource-instrument-sans-5", "instrument-sans", ["400-normal", "400-italic", "700-normal"])]:
        d = next(p for p in os.listdir(FONTS) if p.startswith(pkg) and os.path.isdir(os.path.join(FONTS, p)))
        for w in ws:
            shutil.copy(os.path.join(FONTS, d, "files", f"{fam}-latin-{w}.woff2"), os.path.join(OUT, "fonts"))
    shutil.copy(os.path.join(HERE, "annuels.css"), os.path.join(OUT, "style.css"))
    open(os.path.join(OUT, "index.html"), "w").write(index_page())
    for m in DATA:
        os.makedirs(os.path.join(OUT, m["key"]))
        open(os.path.join(OUT, m["key"], "index.html"), "w").write(year_page(m))
    open(os.path.join(OUT, "404.html"), "w").write(page("Page introuvable · Les albums de l'année", "", top_bar() +
        '<main><section class="hub"><h1>Page<br>introuvable</h1><p><a href="/">Retour aux années</a></p></section></main>', "#141414", "hub-page"))
    open(os.path.join(OUT, "CNAME"), "w").write("albums.lref.fr\n")
    open(os.path.join(OUT, "README.md"), "w").write("# Les albums de l'année\n\nTops albums annuels de Le Rap en France (2013–2022), restaurés depuis la Wayback Machine. Site statique généré par `build_annuels.py`.\n")
    print("ok", len(DATA))


if __name__ == "__main__":
    build()
