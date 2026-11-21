"""Maquette D « Le fonds » : la une montre le fonds entier (une case par article), des tiroirs de catalogue
pour les rubriques, des fiches bristol pour les pièces. Génère maquette-d.html et une page article."""
import json, re, html, os, collections
R = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
S = json.load(open("/tmp/S.json"))
esc = html.escape
MOIS = "janvier février mars avril mai juin juillet août septembre octobre novembre décembre".split()
SEC = [("classements", "Classements", "CLA"), ("dossiers", "Dossiers", "DOS"), ("interviews", "Interviews", "ITW"),
       ("chroniques", "Chroniques", "CHR"), ("billets", "Billets d'humeur", "BIL"), ("selections", "Sélections", "SEL"),
       ("actus", "Actus", "ACT")]
CODE = {k: c for k, _, c in SEC}
LAB = {k: l for k, l, _ in SEC}
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


def head(title, pre, extra=""):
    nav = "".join(f'<a href="{pre}rubrique/{k}.html"><i class="k-{k}"></i>{esc(l)}</a>' for k, l, _ in SEC)
    return f"""<!DOCTYPE html><html lang="fr"><head><meta charset="utf-8"><meta name="robots" content="noindex">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(title)}</title>
<link rel="stylesheet" href="{pre}maquettes/d.css?v=3">{extra}</head><body>
<header class="bar"><a class="logo" href="{pre}maquette-d.html"><b>LREF</b><span>Fonds Le Rap en France</span></a>
<nav>{nav}<a href="{pre}articles.html">Tout le fonds</a></nav>
<form action="{pre}articles.html"><input name="q" type="search" placeholder="Chercher dans le fonds" aria-label="Rechercher"></form></header>"""


FOOT = """<footer class="ft"><div class="ft-in"><p class="ft-t">Provenance</p><p>Le Rap en France, média web consacré au rap français, fondé en 2011 par Stéphane Fortems. Le site a disparu après un piratage. Ce fonds a été reconstitué en 2026 à partir des copies conservées par la Wayback Machine d'Internet Archive. Les textes appartiennent à leurs auteurs.</p>
<p class="ft-l"><a href="https://90.lref.fr/">Top 100 années 90</a><a href="https://2000.lref.fr/">Top 100 années 2000</a><a href="https://albums.lref.fr/">Les albums de l'année</a><a href="https://2016.lref.fr/">Une année 2016</a><a href="a-propos.html">À propos du fonds</a></p></div></footer>"""


def switch(art):
    pre = "../../" if art else ""
    o = [(f"{pre}maquette-{k}.html" if not art else f"maquette-{k}.html", v) for k, v in
         [("a", "A"), ("b", "B"), ("c", "C"), ("d", "D · Le fonds")]]
    other = f'<a href="{pre}maquette-d.html">Voir la une</a>' if art else '<a href="a/lunatic-dans-la-legende/maquette-d.html">Voir un article</a>'
    return '<div class="sw">' + "".join(f'<a href="{h}"{" aria-current=page" if "maquette-d" in h else ""}>{v}</a>' for h, v in o) + f"<span></span>{other}</div>"


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
pieces = fiche(fp[0], True, hrefs.get(fp[0]["s"])) + "".join(fiche(a, False, hrefs.get(a["s"])) for a in fp[1:])
au = collections.Counter(a["a"] for a in S if a["a"] and a["a"] != "La Rédaction")
plumes = "".join(f'<li><a href="articles.html?au={esc(n)}"><span>{esc(n)}</span><i></i><b>{c}</b></a></li>' for n, c in sorted(au.most_common(30), key=lambda x: x[0].lower()))

body = f"""<main>
<section class="vault">
 <div class="v-in">
  <div class="v-head">
   <p class="v-kick">Le Rap en France · 2011–2023</p>
   <h1>Douze ans<br>de rap français.</h1>
   <p class="v-txt">Des chroniques d'albums, des interviews d'artistes installés comme de ceux qu'on découvrait, des dossiers de fond et des classements qui faisaient débat, écrits par une trentaine de plumes bénévoles. Chaque case ci-dessous est un article, rangé dans son année : survolez pour lire la fiche, cliquez pour l'ouvrir.</p>
   <div class="legend">{legend}</div>
  </div>
  <aside class="peek" aria-live="polite"><div class="peek-card" id="peek"><span class="cote">LREF·…·…·0000</span><span class="ft-title">Survolez une case du fonds</span><span class="meta"><span>Rubrique</span><span>Auteur</span><span>Date</span></span></div></aside>
 </div>
 <div class="wall" id="wall">{"".join(cells)}</div>
</section>
<section class="rubs"><div class="rubs-in"><p class="v-kick">Les rubriques</p>{drawers}<a class="rub all" href="articles.html"><span class="r-name">Tout le fonds</span><span class="r-meta"><b>1 193</b> articles<br>recherche</span></a></div></section>
<section class="blk"><header class="blk-h"><h2>Pièces remarquables</h2><p>Une sélection pour commencer.</p></header><div class="pieces">{pieces}
<a class="fiche fold" href="top-100-annees-90.html"><span class="cote">LREF·CLA·DOSSIER SPÉCIAL</span><span class="ft-title">Les 100 meilleurs albums des années 90</span><span class="meta"><span>Classement complet</span><span>100 notices</span></span></a>
<a class="fiche fold" href="https://albums.lref.fr/"><span class="cote">LREF·CLA·2012–2022</span><span class="ft-title">Les albums de l'année</span><span class="meta"><span>Dix bilans annuels</span></span></a></div></section>
<section class="blk"><header class="blk-h"><h2>Tiré au hasard</h2><p>Six fiches sorties du fonds, au hasard. <button type="button" id="draw">Tirer six autres fiches</button></p></header><div class="pieces rnd" id="rnd"></div></section>
<section class="blk"><header class="blk-h"><h2>Index des plumes</h2><p>{len(au) + 1} auteurs ont écrit pour LREF. Les trente plus présents, par ordre alphabétique.</p></header><ol class="plumes">{plumes}</ol></section>
</main>
{FOOT}{switch(False)}
<script>
const M={json.dumps(mini, ensure_ascii=False, separators=(",", ":"))};
const LAB={json.dumps(LAB, ensure_ascii=False)};
const e=s=>String(s).replace(/[&<>"]/g,c=>({{"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}}[c]));
const card=(a,tag)=>`<${{tag}} class="${{tag=="a"?"fiche ":""}}k-${{a[4]}}"${{tag=="a"?` href="a/${{a[0]}}/"`:""}}>${{a[6]?`<span class="snap"><img src="${{e(a[6])}}" alt="" onerror="this.parentNode.remove()"></span>`:""}}<span class="cote">${{a[5]}}</span><span class="ft-title">${{e(a[1])}}</span><span class="meta"><span>${{e(LAB[a[4]]||"")}}</span><span>${{e(a[3]||"La Rédaction")}}</span><span>${{e(a[2])}}</span></span></${{tag}}>`;
const peek=document.getElementById("peek"),wall=document.getElementById("wall");
const show=t=>{{const a=t&&t.dataset.n&&M[t.dataset.n];if(!a)return;peek.className="peek-card k-"+a[4];peek.innerHTML=card(a,"div").replace(/^<div[^>]*>|<\\/div>$/g,"")}};
wall.addEventListener("mouseover",ev=>show(ev.target.closest("a")));wall.addEventListener("focusin",ev=>show(ev.target));
document.querySelectorAll(".legend button").forEach(b=>b.addEventListener("click",()=>{{const on=b.getAttribute("aria-pressed")!="true";document.querySelectorAll(".legend button").forEach(x=>x.setAttribute("aria-pressed","false"));b.setAttribute("aria-pressed",on);wall.dataset.f=on?b.dataset.k:""}}));
const ks=Object.keys(M),rnd=document.getElementById("rnd");
const draw=()=>{{const p=[];while(p.length<6){{const k=ks[Math.random()*ks.length|0];if(!p.includes(k))p.push(k)}}rnd.innerHTML=p.map(k=>card(M[k],"a")).join("")}};
document.getElementById("draw").addEventListener("click",draw);draw();
</script></body></html>"""
open(os.path.join(R, "maquette-d.html"), "w").write(head("Le fonds Le Rap en France – maquette D", "") + body)

# ---------------- article ----------------
slug = "lunatic-dans-la-legende"
a = by[slug]
src = open(os.path.join(R, "a", slug, "index.html")).read()
prose = src[src.index('<div class="prose">'):src.index('<footer class="story-foot">')]
mins = re.search(r'class="read">(\d+) min', src).group(1)
orig = re.sub(r"^https?://web\.archive\.org/web/\d+/", "", a["w"]).replace("http://", "").rstrip("/")
Y = years[a["d"][:4]]
pos = Y.index(a) + 1
mw = "".join(f'<a class="k-{b["k"]}{" here" if b is a else ""}" href="../../a/{b["s"]}/" title="{esc(b["t"])}"{" aria-current=page" if b is a else ""}></a>' for b in Y)
prev, nxt = (S[a["n"] - 2] if a["n"] > 1 else None), (S[a["n"]] if a["n"] < len(S) else None)
def nav(b, lab, cls):
    return f'<a class="cn {cls} k-{b["k"]}" href="../../a/{b["s"]}/"><span class="cn-l">{lab}</span><span class="cote">{b["cote"]}</span><span class="cn-t">{esc(b["t"])}</span><span class="cn-m">{esc(b["a"] or "La Rédaction")}, {esc(b["f"])}</span></a>'
more = [b for b in S if b["k"] == a["k"] and b["s"] != slug and b["i"]][-40:][::7][:3]
art = f"""<main class="art k-{a['k']}">
<header class="ah"><div class="ah-in">
 <div class="ah-main">
  <p class="ah-k"><i class="k-{a['k']}"></i><a href="../../rubrique/{a['k']}.html">{esc(LAB[a['k']])}</a><span>{a['cote']}</span></p>
  <h1>{esc(a['t'])}</h1>
  <p class="ah-by">Par <a href="../../articles.html?au={esc(a['a'])}">{esc(a['a'])}</a> · {esc(a['f'])} · {mins} min de lecture</p>
 </div>
 <aside class="ah-wall" aria-label="Position dans le fonds">
  <p class="aw-t"><b>{a['d'][:4]}</b> {pos}<sup>e</sup> article sur {len(Y)}</p>
  <div class="aw">{mw}</div>
  <p class="aw-n">N° {a['n']} sur {len(S):} dans le fonds</p>
 </aside>
</div></header>
{f'<figure class="acov"><img src="{esc(a["i"])}" alt="" onerror="this.parentNode.remove()"></figure>' if a['i'] else ''}
<div class="abody">
 <aside class="notice"><p class="n-h">Notice</p><dl>
  <dt>Cote</dt><dd>{a['cote']}</dd>
  <dt>Série</dt><dd>{esc(LAB[a['k']])}</dd>
  <dt>Auteur</dt><dd>{esc(a['a'])}</dd>
  <dt>Publication</dt><dd>{esc(a['f'])}</dd>
  <dt>Copie Wayback</dt><dd><a href="{esc(a['w'])}">{esc(a['cap'])}</a></dd>
  <dt>Adresse d'origine</dt><dd><s>{esc(orig)}</s></dd>
 </dl></aside>
 {prose}
</div>
<nav class="chrono" aria-label="Dans l'ordre du fonds">{nav(prev, "← Article précédent", "p") if prev else ""}{nav(nxt, "Article suivant →", "n") if nxt else ""}</nav>
<section class="blk near"><header class="blk-h"><h2>Dans la même série</h2></header><div class="pieces">{"".join(fiche(b).replace('href="a/', 'href="../../a/') for b in more)}</div></section>
</main>
{FOOT.replace('href="a-propos', 'href="../../a-propos')}{switch(True)}</body></html>"""
open(os.path.join(R, "a", slug, "maquette-d.html"), "w").write(head(a["t"] + " – maquette D", "../../") + art)
print("ok", len(S))
