"""Finalisation du site (design « Le fonds ») : à lancer après build.py.
Réécrit la une (index.html) et toutes les pages articles a/<slug>/index.html."""
import json, re, html, os, collections, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import typo
R = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = json.load(open(os.path.join(R, "search.json"), encoding="utf-8"))
PAGES = {}
for a in S:
    h = open(os.path.join(R, "a", a["s"], "index.html"), encoding="utf-8").read()
    PAGES[a["s"]] = h
    m = re.search(r'<figure class="(?:cover|acov)"><img src="([^"]+)"', h); a["i"] = m.group(1) if m else ""
    m = re.search(r'class="src">.*?href="([^"]+)"', h) or re.search(r'<dt>Copie Wayback</dt><dd><a href="([^"]+)"', h); a["w"] = m.group(1) if m else ""
esc = html.escape
MOIS = "janvier février mars avril mai juin juillet août septembre octobre novembre décembre".split()
SEC = [("classements", "Classements", "CLA"), ("dossiers", "Dossiers", "DOS"), ("interviews", "Interviews", "ITW"),
       ("chroniques", "Chroniques", "CHR"), ("billets", "Billets d'humeur", "BIL"), ("selections", "Sélections", "SEL"),
       ("actus", "Actus", "ACT")]
CODE = {k: c for k, _, c in SEC}
LAB = {k: l for k, l, _ in SEC}
LAB["divers"] = "Divers"
S.sort(key=lambda a: a["d"])
for n, a in enumerate(S, 1):
    a["n"] = n
    a["cote"] = f"LREF·{CODE.get(a['k'], 'DIV')}·{a['d'][:4]}·{n:04d}"
    m = re.search(r"/web/(\d{4})(\d{2})(\d{2})", a["w"])
    a["cap"] = f"{int(m.group(3))} {MOIS[int(m.group(2)) - 1]} {m.group(1)}" if m else ""
by = {a["s"]: a for a in S}
years = collections.defaultdict(list)
for a in S:
    years[a["d"][:4]].append(a)


def head(title, pre, extra="", desc="", img=""):
    nav = "".join(f'<a href="{pre}rubrique/{k}.html"><i class="k-{k}"></i>{esc(l)}</a>' for k, l, _ in SEC)
    return f"""<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)}</title><meta name="description" content="{esc(desc)}"><meta property="og:title" content="{esc(title)}"><meta property="og:description" content="{esc(desc)}">{f'<meta property="og:image" content="{esc(img)}">' if img else ""}<meta name="theme-color" content="#1E3350">
<link rel="stylesheet" href="{pre}style.css?v=5">{extra}</head><body>
<header class="bar"><a class="logo" href="{pre}index.html"><b>LREF</b><span>Fonds Le Rap en France</span></a>
<nav>{nav}<a href="{pre}articles.html">Tout le fonds</a></nav>
<form action="{pre}articles.html"><input name="q" type="search" placeholder="Chercher dans le fonds" aria-label="Rechercher"></form></header>"""


FOOT0 = """<footer class="ft"><div class="ft-in"><p class="ft-t">Provenance</p><p>Le Rap en France, média web consacré au rap français, fondé en 2011 par Stéphane Fortems. Le site a disparu après un piratage. Ce fonds a été reconstitué en 2026 à partir des copies conservées par la Wayback Machine d'Internet Archive. Les textes appartiennent à leurs auteurs.</p>
<p class="ft-l"><a href="https://90.lref.fr/">Top 100 années 90</a><a href="https://2000.lref.fr/">Top 100 années 2000</a><a href="https://albums.lref.fr/">Les albums de l'année</a><a href="https://2016.lref.fr/">Une année 2016</a><a href="{pre}a-propos.html">À propos du fonds</a><a href="{pre}jul-marseille.html">Jul &amp; Marseille, la carte</a></p></div></footer>"""
FOOT = FOOT0.replace("{pre}", "")


# ---------------- une ----------------
cells = []
for y in sorted(years):
    L = years[y]
    c = "".join(f'<a class="k-{a["k"]}" href="a/{a["s"]}/" data-n="{a["n"]}" aria-label="{esc(a["t"])}"></a>' for a in L)
    cells.append(f'<div class="col"><div class="cells">{c}</div><p class="yl"><b>{y}</b><span>{len(L)}</span></p></div>')
mini = {a["n"]: [a["s"], a["t"], a["f"], a["a"], a["k"], a["cote"], a["i"]] for a in S}
legend = "".join(f'<button type="button" data-k="{k}"><i class="k-{k}"></i>{esc(l)} <span>{sum(1 for a in S if a["k"] == k)}</span></button>' for k, l, _ in SEC)


def rng(k):
    L = [a for a in S if a["k"] == k]
    return f'{L[0]["d"][:4]}–{L[-1]["d"][:4]}', len(L)


drawers = ""
for k, l, c in SEC:
    r, n = rng(k)
    ims = [a["i"] for a in S if a["k"] == k and a["i"]][::-1][:10]
    tr = "".join(f'<img src="{esc(u)}" alt="" loading="lazy" onerror="this.remove()">' for u in ims)
    drawers += f'<a class="rub k-{k}" href="rubrique/{k}.html"><span class="r-strip" aria-hidden="true"><span class="r-track">{tr}{tr}</span></span><span class="r-name">{esc(l)}</span><span class="r-meta"><b>{n}</b> articles<br>{r}</span></a>'



def fiche(a, big=False, extra_href=None):
    img = f'<span class="snap"><img src="{esc(a["i"])}" alt="" loading="lazy" onerror="this.parentNode.remove()"></span>' if a["i"] else ""
    return f"""<a class="fiche k-{a['k']}{' big' if big else ''}" href="{extra_href or 'a/' + a['s'] + '/'}">{img}<span class="cote">{a['cote']}</span>
<span class="ft-title">{esc(a['t'])}</span><span class="meta"><span>{esc(LAB.get(a['k'], ''))}</span><span>{esc(a['a'] or 'La Rédaction')}</span><span>{esc(a['f'])}</span></span></a>"""


picks = ["les-100-meilleurs-albums-des-annees-2000-le-top-10", "lref-carte-de-marseille-par-jul", "lunatic-dans-la-legende",
         "booba-et-la-religion-oecumenisme-peches-et-paraboles", "dossier-sante-mentale-fin-silence-rap-francais"]
fp = [by[s] for s in picks if s in by]
hrefs = {"les-100-meilleurs-albums-des-annees-2000-le-top-10": "top-100-annees-2000.html", "lref-carte-de-marseille-par-jul": "jul-marseille.html"}
prow = [(hrefs.get(x["s"], "a/" + x["s"] + "/"), x["k"], LAB[x["k"]], x["t"], f'{x["a"] or "La Rédaction"}, {x["f"]}', x["i"]) for x in fp]
prow[1:1] = [("top-100-annees-90.html", "classements", "Classements", "Les 100 meilleurs albums des années 90", "La Rédaction, cent notices", fp[0]["i"]),
             ("https://albums.lref.fr/", "classements", "Classements", "Les albums de l'année, de 2012 à 2022", "Dix bilans annuels", "")]
pieces = "".join(f'<a class="pc k-{k}" href="{h}" data-img="{esc(i)}"><span class="pc-k"><i class="k-{k}"></i>{esc(l)}</span><span class="pc-t">{esc(t)}</span><span class="pc-m">{esc(m)}</span></a>' for h, k, l, t, m, i in prow)
au = collections.Counter(a["a"] for a in S if a["a"] and a["a"] != "La Rédaction")
plumes = "".join(f'<li><a href="articles.html?au={esc(n)}"><span>{esc(n)}</span><i></i><b>{c}</b></a></li>' for n, c in sorted(au.most_common(30), key=lambda x: x[0].lower()))

names = sorted(au.most_common(30), key=lambda x: x[0].lower())
def mqs(L, hid):
    return "".join(f'<a href="articles.html?au={esc(n)}"{" tabindex=-1 aria-hidden=true" if hid else ""}>{esc(n)}<sup>{c}</sup></a>' for n, c in L)
mq1, mq1h = mqs(names[::2], False), mqs(names[::2], True)
mq2, mq2h = mqs(names[1::2], False), mqs(names[1::2], True)
body = f"""<main>
<section class="vault">
 <div class="v-in">
  <div class="v-head">
   <p class="v-kick">Le Rap en France · 2011–2023</p>
   <h1>Douze ans<br>de rap français.</h1>
   <p class="v-txt">Des chroniques d'albums, des interviews d'artistes installés comme de ceux qu'on découvrait, des dossiers de fond et des classements qui faisaient débat, écrits au fil des ans par quatre-vingts plumes bénévoles. Chaque case ci-dessous est un article, rangé dans son année : survolez pour lire la fiche, cliquez pour l'ouvrir.</p>
   <div class="legend">{legend}</div>
  </div>
  <aside class="peek" aria-live="polite"><div class="peek-card" id="peek"><span class="cote">LREF·…·…·0000</span><span class="ft-title">Survolez une case du fonds</span><span class="meta"><span>Rubrique</span><span>Auteur</span><span>Date</span></span></div></aside>
 </div>
 <div class="wall" id="wall">{"".join(cells)}</div>
</section>
<section class="rubs"><div class="rubs-in"><p class="v-kick">Les rubriques</p>{drawers}<a class="rub all" href="articles.html"><span class="r-name">Tout le fonds</span><span class="r-meta"><b>1 193</b> articles<br>recherche</span></a></div></section>
<section class="must"><div class="must-in"><header class="sh"><p class="v-kick">Pour commencer</p><h2>Les incontournables</h2></header><div class="pcs" id="pcs">{pieces}</div></div></section>
<section class="slot" id="slot"><div class="slot-in">
 <header class="sh"><p class="v-kick">Tiré au hasard</p><h2>Un article,<br>au pif.</h2><button type="button" id="draw">Tirer un article</button></header>
 <a class="sl-card" id="sl" href="#"><span class="sl-img" id="sl-img"></span><span class="sl-txt"><span class="sl-k" id="sl-k"></span><span class="sl-t" id="sl-t"></span><span class="sl-m" id="sl-m"></span></span></a>
</div></section>
<section class="crew"><header class="sh crew-h"><p class="v-kick">La rédaction</p><h2>{len(au) + 1} plumes</h2></header>
 <div class="mq"><div class="mq-t">{mq1}{mq1h}</div></div><div class="mq rev"><div class="mq-t">{mq2}{mq2h}</div></div>
</section>
</main>
{FOOT}
<script>
const M={json.dumps(mini, ensure_ascii=False, separators=(",", ":"))};
const LAB={json.dumps(LAB, ensure_ascii=False)};
const e=s=>String(s).replace(/[&<>"]/g,c=>({{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}}[c]));
const card=(a,tag)=>`<${{tag}} class="${{tag=="a"?"fiche ":""}}k-${{a[4]}}"${{tag=="a"?` href="a/${{a[0]}}/"`:""}}>${{a[6]?`<span class="snap"><img src="${{e(a[6])}}" alt="" onerror="this.parentNode.remove()"></span>`:""}}<span class="cote">${{a[5]}}</span><span class="ft-title">${{e(a[1])}}</span><span class="meta"><span>${{e(LAB[a[4]]||"")}}</span><span>${{e(a[3]||"La Rédaction")}}</span><span>${{e(a[2])}}</span></span></${{tag}}>`;
const peek=document.getElementById("peek"),wall=document.getElementById("wall");
const show=t=>{{const a=t&&t.dataset.n&&M[t.dataset.n];if(!a)return;peek.className="peek-card k-"+a[4];peek.innerHTML=card(a,"div").replace(/^<div[^>]*>|<\\/div>$/g,"")}};
wall.addEventListener("mouseover",ev=>show(ev.target.closest("a")));wall.addEventListener("focusin",ev=>show(ev.target));
document.querySelectorAll(".legend button").forEach(b=>b.addEventListener("click",()=>{{const on=b.getAttribute("aria-pressed")!="true";document.querySelectorAll(".legend button").forEach(x=>x.setAttribute("aria-pressed","false"));b.setAttribute("aria-pressed",on);wall.dataset.f=on?b.dataset.k:""}}));
const ks=Object.keys(M),slot=document.getElementById("slot");
const sl={{c:document.getElementById("sl"),i:document.getElementById("sl-img"),k:document.getElementById("sl-k"),t:document.getElementById("sl-t"),m:document.getElementById("sl-m")}};
const pickk=()=>M[ks[Math.random()*ks.length|0]];
const put=a=>{{slot.className="slot k-"+a[4];sl.k.textContent=(LAB[a[4]]||"")+"  ·  "+a[5];sl.t.textContent=a[1];sl.m.textContent=(a[3]||"La Rédaction")+", "+a[2];sl.c.href="a/"+a[0]+"/"}};
const still=matchMedia("(prefers-reduced-motion:reduce)").matches;
const draw=()=>{{let n=still?0:14;const fin=pickk();sl.c.classList.add("spin");sl.i.innerHTML="";
 const step=()=>{{if(n-->0){{put(pickk());setTimeout(step,45+(14-n)*9)}}else{{put(fin);sl.c.classList.remove("spin");if(fin[6])sl.i.innerHTML=`<img src="${{e(fin[6])}}" alt="" onerror="this.remove()">`}}}};step()}};
document.getElementById("draw").addEventListener("click",draw);draw();
</script></body></html>"""
open(os.path.join(R, "index.html"), "w", encoding="utf-8").write(head("Le Rap en France – douze ans de rap français, 2011–2023", "", "", "Archives du média Le Rap en France (LREF) : 1 193 chroniques, interviews, dossiers et classements sur le rap français, 2011–2023.") + body.replace('<main>', '<main class="home">', 1))

# ---------------- article ----------------
for a in S:
  slug = a["s"]
  src = PAGES[slug]
  prose = src[src.index('<div class="prose">'):src.index('<footer class="story-foot">')]
  prose = typo.clean(prose, interview=a["k"] == "interviews")
  mins = re.search(r'class="read">(\d+) min', src).group(1)
  orig = re.sub(r"^https?://web\.archive\.org/web/\d+/", "", a["w"]).replace("http://", "").rstrip("/")
  Y = years[a["d"][:4]]
  pos = Y.index(a) + 1
  mw = "".join(f'<a class="k-{b["k"]}{" here" if b is a else ""}" href="../../a/{b["s"]}/" title="{esc(b["t"])}"{" aria-current=page" if b is a else ""}></a>' for b in Y)
  prev, nxt = (S[a["n"] - 2] if a["n"] > 1 else None), (S[a["n"]] if a["n"] < len(S) else None)
  def nav(b, lab, cls):
      return f'<a class="cn {cls} k-{b["k"]}" href="../../a/{b["s"]}/"><span class="cn-l">{lab}</span><span class="cote">{b["cote"]}</span><span class="cn-t">{esc(b["t"])}</span><span class="cn-m">{esc(b["a"] or "La Rédaction")}, {esc(b["f"])}</span></a>'
  more = sorted((b for b in S if b["k"] == a["k"] and b is not a and b["i"]), key=lambda b: abs(b["n"] - a["n"]))[:3]
  tg = re.search(r'<p class="tags">.*?</p>', src)
  who = a["a"] or "La Rédaction"
  art = f"""<main class="art k-{a['k']}">
  <header class="ah"><div class="ah-in">
   <div class="ah-main">
    <p class="ah-k"><i class="k-{a['k']}"></i><a href="../../rubrique/{a['k'] if a['k'] != 'divers' else 'actus'}.html">{esc(LAB[a['k']])}</a><span>{a['cote']}</span></p>
    <h1>{esc(a['t'])}</h1>
    <p class="ah-by">Par <a href="../../articles.html?au={esc(who)}">{esc(who)}</a> · {esc(a['f'])} · {mins} min de lecture</p>
   </div>
   <aside class="ah-wall" aria-label="Position dans le fonds">
    <p class="aw-t"><b>{a['d'][:4]}</b> {pos}<sup>e</sup> article sur {len(Y)}</p>
    <div class="aw">{mw}</div>
    <p class="aw-n">N° {a['n']} sur {len(S)} dans le fonds</p>
   </aside>
  </div></header>
  {f'<figure class="acov"><img src="{esc(a["i"])}" alt="" onerror="this.parentNode.remove()"></figure>' if a['i'] else ''}
  <div class="abody">
   <aside class="notice"><p class="n-h">Notice</p><dl>
    <dt>Cote</dt><dd>{a['cote']}</dd>
    <dt>Série</dt><dd>{esc(LAB[a['k']])}</dd>
    <dt>Auteur</dt><dd>{esc(who)}</dd>
    <dt>Publication</dt><dd>{esc(a['f'])}</dd>
    <dt>Copie Wayback</dt><dd><a href="{esc(a['w'])}">{esc(a['cap'])}</a></dd>
    <dt>Adresse d'origine</dt><dd><s>{esc(orig)}</s></dd>
   </dl></aside>
   <div class="txt">{prose}<footer class="story-foot">{tg.group(0) if tg else ""}<p class="src">Article publié sur lerapenfrance.fr. <a href="{esc(a['w'])}">Voir la copie d'archive</a></p></footer></div>
  </div>
  <nav class="chrono" aria-label="Dans l'ordre du fonds">{nav(prev, "← Article précédent", "p") if prev else ""}{nav(nxt, "Article suivant →", "n") if nxt else ""}</nav>
  <section class="blk near"><header class="blk-h"><h2>Dans la même série</h2></header><div class="pieces">{"".join(fiche(b).replace('href="a/', 'href="../../a/') for b in more)}</div></section>
  </main>
  {FOOT0.replace('{pre}', '../../')}</body></html>"""
  open(os.path.join(R, "a", slug, "index.html"), "w", encoding="utf-8").write(head(a["t"] + " – Le Rap en France", "../../", "", a.get("x", ""), a["i"]) + art)
print("finalize ok", len(S))

# ---------------- page Classements (tranches façon albums.lref.fr) ----------------
ANN = json.load(open(os.path.join(R, "data", "tops-albums-annuels.json"), encoding="utf-8"))
def ann_cover(key):
    for y in ANN:
        if y["key"] == key:
            return y["items"][0].get("img", "")
    return ""
def img_of(slug):
    return by[slug]["i"] if slug in by else ""
BIG = [
    ("https://90.lref.fr/", "#FFD23F", "Années 90", "Les 100 meilleurs albums des années 90", "100 disques, de Dee Nasty à L'école du micro d'argent", img_of("les-100-meilleurs-albums-des-annees-90-100-a-91")),
    ("https://2000.lref.fr/", "#FF6A3D", "Années 2000", "Les 100 meilleurs albums des années 2000", "100 disques, un texte pour chacun", img_of("les-100-meilleurs-albums-des-annees-2000-le-top-10")),
    ("https://albums.lref.fr/", "#7090FF", "2012–2022", "Les albums de l'année", "Dix bilans annuels de la rédaction", ann_cover("2017")),
    ("https://2016.lref.fr/", "#FF8AC8", "2016", "Une année 2016", "116 morceaux choisis par la rédaction", img_of("nos-morceaux-preferes-2016")),
]
MOISL = {m: m.capitalize() for m in MOIS}
def short(a):
    t = a["t"].lower()
    y = re.findall(r"20\d\d", a["t"])
    yr = y[-1] if y else a["d"][:4]
    for m in MOIS:
        if m in t:
            return f"{m.capitalize()[:4]}{'.' if len(m) > 4 else ''} {yr}"
    if "semestre" in t:
        return f"S1 {yr}"
    m = re.search(r"(premier|second|troisième|1er)\s+trimestre", t)
    if m:
        return f"T{ {'premier': 1, '1er': 1, 'second': 2, 'troisième': 3}[m.group(1)] } {yr}"
    if "vacs" in t:
        return f"Déc. {yr}"
    return yr
YC = {"2014": "#FFD23F", "2015": "#FFA024", "2016": "#FF6A3D", "2017": "#FF8AC8", "2018": "#E07BFF", "2019": "#A98BFF",
      "2020": "#7090FF", "2021": "#56C8FF", "2022": "#7CF0E0", "2023": "#9BE564"}
def label(a):
    t = a["t"].lower(); p = short(a)
    if "coup" in t: return "Cœur " + p
    if "eps" in t: return "EPs " + p
    if "nuit" in t: return "Nuit " + p
    if "featuring" in t: return "Feat. " + p
    if "clips" in t: return "Clips " + p
    if "visuels" in t: return "Visuels " + p
    if "playlist" in t: return "Mondial " + p
    return p
def kind(a):
    t = a["t"].lower()
    if "beatmaker" in t: return "beat"
    if "featuring" in t or "clips" in t or "visuels" in t or "playlist" in t: return "autres"
    if "morceaux" in t or "sons" in t: return "morceaux"
    if "100 meilleurs albums" in t or "top 100" in t: return None
    return "albums"
GROUPS = [("albums", "Albums et projets", "Les bilans de l'année, des semestres et des trimestres, et les coups de cœur de la rédaction.", "#FFD23F"),
          ("morceaux", "Morceaux", "Les sons de l'année, puis du mois, en 2016 et 2017.", "#FF8AC8"),
          ("beat", "Beatmakers", "Les producteurs de l'année, de 2014 à 2018.", "#9BE564"),
          ("autres", "Featurings, clips et visuels", "Les à-côtés du rap de l'année.", "#7CE0FF")]
CL = [a for a in S if a["k"] == "classements"]
def spine(a, c):
    im = f'<span class="cv"><img src="{esc(a["i"])}" alt="" loading="lazy" onerror="this.remove()"></span>' if a["i"] else '<span class="cv"></span>'
    return f'<li style="--c:{c}"><a href="../a/{a["s"]}/">{im}<span class="yr">{esc(label(a))}</span><span class="meta"><small>{esc(a["f"])}</small><b>{esc(a["t"].rstrip(" –"))}</b><em>{esc(a["a"] or "La Rédaction")}</em></span></a></li>'
shelves = ""
for g, lab, txt, col in GROUPS:
    L = [a for a in CL if kind(a) == g]
    L.sort(key=lambda a: a["d"])
    if not L:
        continue
    shelves += f'<section class="shelf"><header class="sh-h"><h2>{esc(lab)}</h2><p>{esc(txt)} <span>{len(L)} classements</span></p></header><ul class="spines">{"".join(spine(a, YC.get(re.findall(r"20\d\d", label(a))[-1], col)) for a in L)}</ul></section>'
big = "".join(f'<li style="--c:{c}"><a href="{h}">{f"<span class=cv><img src={chr(34)}{esc(i)}{chr(34)} alt={chr(34)}{chr(34)} loading=lazy onerror={chr(34)}this.remove(){chr(34)}></span>" if i else "<span class=cv></span>"}<span class="yr">{esc(y)}</span><span class="meta"><small>Sous-site</small><b>{esc(t)}</b><em>{esc(d)}</em></span></a></li>' for h, c, y, t, d, i in BIG)
body = f"""<main class="cls">
<header class="cls-h"><div class="cls-in"><p class="v-kick">Le Rap en France · {len(CL)} classements</p><h1>Classements</h1>
<p class="cls-t">Douze ans de tops, de bilans et de coups de cœur. Survolez une tranche pour l'ouvrir, cliquez pour lire.</p>
<ul class="spines big">{big}</ul></div></header>
<div class="cls-in">{shelves}</div>
</main>
{FOOT0.replace('{pre}', '../')}</body></html>"""
open(os.path.join(R, "rubrique", "classements.html"), "w", encoding="utf-8").write(
    head("Classements – Le Rap en France", "../", "", "Les classements de Le Rap en France : tops des années 90 et 2000, albums de l'année, morceaux, beatmakers.").replace('<a href="../rubrique/classements.html">', '<a href="../rubrique/classements.html" aria-current="page">') + body)
print("classements ok", len(CL))
