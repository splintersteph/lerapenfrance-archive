"""Harmonisation typographique du texte des articles (appelé par finalize.py).

Règles :
- <b>/<i> deviennent <strong>/<em> ; le soulignement (<u>) devient de l'italique (titres d'œuvres).
- <strong><em> et <em><strong> : un seul ordre, gras à l'extérieur.
- Intertitres : tous les niveaux de titre deviennent <h3>, sans gras imbriqué. Un paragraphe court entièrement
  en gras (hors interviews) devient un intertitre.
- Interviews : les paragraphes entièrement en gras sont les questions -> <p class="q">.
- Premier paragraphe entièrement en gras : chapeau -> <p class="chapo">.
- Doubles <br> : coupés en paragraphes. Paragraphes vides ou réduits à un point : supprimés.
- Dans le texte (jamais dans les attributs) : espaces insécables multiples, points de suspension, tiret entre
  espaces -> tiret demi-cadratin, espace avant virgule, guillemet ouvrant mis à la place d'un fermant,
  apostrophes et guillemets droits.
"""
import re
from bs4 import BeautifulSoup, NavigableString, Comment

NB = " "
NNB = " "


def _text_fix(s):
    s = s.replace("  ", NB)
    s = re.sub(r"[  ]{2,}", " ", s)
    s = s.replace("...", "…")
    s = re.sub(r"(?<=\S) - (?=\S)", " – ", s)
    s = re.sub(r"(?<=\w)'(?=\w)", "’", s)
    s = re.sub(r"\s+,", ",", s)
    s = re.sub(r"(?<=[^\s«])\s*«(?=\s*[,.;:!?)\]])", NB + "»", s)
    s = re.sub(r"^\s*«(?=\s*[,.;:!?)\]])", NB + "»", s)
    s = re.sub(r'(^|[\s(\[])"(\S[^"]{0,300}?\S|\S)"(?=$|[\s.,;:!?)\]])', lambda m: f"{m.group(1)}«{NB}{m.group(2)}{NB}»", s)
    return s


def _only_bold(p):
    kids = [k for k in p.contents if not (isinstance(k, NavigableString) and not k.strip())]
    if len(kids) == 1 and getattr(kids[0], "name", None) == "a":
        inner = [k for k in kids[0].contents if not (isinstance(k, NavigableString) and not k.strip())]
        if len(inner) == 1 and getattr(inner[0], "name", None) == "strong":
            a, st = kids[0], inner[0]
            a.name, st.name = "strong", "a"
            st.attrs, a.attrs = dict(a.attrs), {}
            kids = [a]
    return len(kids) == 1 and getattr(kids[0], "name", None) == "strong" and kids[0].get_text(strip=True)


def clean(html, interview=False):
    soup = BeautifulSoup(html, "html.parser")
    root = soup.find("div", class_="prose") or soup
    for c in root.find_all(string=lambda t: isinstance(t, Comment)):
        c.extract()
    for t in root.find_all("b"):
        t.name = "strong"
    for t in root.find_all(["i", "u"]):
        t.name = "em"
        t.attrs = {}
    # em dans em / strong dans strong
    for t in root.find_all(["em", "strong"]):
        if t.parent is not None and t.parent.name == t.name:
            t.unwrap()
    # ordre strong > em
    for em in root.find_all("em"):
        kids = [k for k in em.contents if not (isinstance(k, NavigableString) and not k.strip())]
        if len(kids) == 1 and getattr(kids[0], "name", None) == "strong":
            st = kids[0]
            em.name, st.name = "strong", "em"
    # titres
    for h in root.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
        h.name = "h3"
        h.attrs = {}
        for s in h.find_all("strong"):
            s.unwrap()
        if not h.get_text(strip=True):
            h.decompose()
    # balises de mise en forme vides ou réduites à des espaces
    for t in root.find_all(["strong", "em"]):
        if not t.find(["img", "a", "br"]) and not t.get_text().strip():
            t.unwrap()
    # question en gras suivie d'un <br> puis de la réponse : deux paragraphes
    for p in root.find_all("p"):
        kids = [k for k in p.contents if not (isinstance(k, NavigableString) and not k.strip())]
        if len(kids) >= 3 and getattr(kids[0], "name", None) == "strong" and getattr(kids[1], "name", None) == "br":
            q = kids[0].extract()
            while p.contents and (getattr(p.contents[0], "name", None) == "br" or (isinstance(p.contents[0], NavigableString) and not p.contents[0].strip())):
                p.contents[0].extract()
            newp = soup.new_tag("p")
            newp.append(q)
            p.insert_before(newp)
    # doubles <br> -> paragraphes
    for p in root.find_all("p"):
        if p.find("br") and re.search(r"<br/?>\s*<br/?>", str(p)):
            parts = re.split(r"(?:\s*<br/?>\s*){2,}", p.decode_contents())
            if len(parts) > 1:
                frag = BeautifulSoup("".join(f"<p>{x}</p>" for x in parts if x.strip()), "html.parser")
                p.replace_with(frag)
    # paragraphes vides
    for p in root.find_all("p"):
        if not p.find(["img", "iframe", "a"]) and re.fullmatch(r"[\s. ]*", p.get_text()):
            p.decompose()
    # chapeau, questions, intertitres
    ps = [p for p in root.find_all("p") if not p.find_parent(["blockquote", "li", "figure", "table"])]
    for n, p in enumerate(ps):
        if p.parent is None or p.find_parent("blockquote"):
            continue
        if not _only_bold(p):
            continue
        txt = p.get_text(" ", strip=True)
        if n == 0 and len(txt) > 90:
            p.strong.unwrap()
            p["class"] = "chapo"
        elif interview:
            p.strong.unwrap()
            p["class"] = "q"
        elif len(txt) <= 110 and (len(txt) <= 40 or not txt.endswith((".", ",", ";"))):
            p.strong.unwrap()
            p.name = "h3"
        else:
            p.strong.unwrap()
            p["class"] = "q"
    # guillemet fermant écrit « en tête de citation
    for bq in root.find_all("blockquote"):
        first = bq.find(string=True)
        if first and re.match(r"\s*»\s*", first):
            first.replace_with(re.sub(r"^\s*»\s*", "«" + NB, first))
    # texte
    for t in root.find_all(string=True):
        if isinstance(t, NavigableString) and t.parent.name not in ("script", "style"):
            new = _text_fix(str(t))
            if new != t:
                t.replace_with(new)
    # espaces en bord de balises gras/italique
    out = str(soup)
    out = re.sub(r"<(strong|em)>(\s+)", r"\2<\1>", out)
    out = re.sub(r"(\s+)</(strong|em)>", r"</\2>\1", out)
    out = re.sub(r"<(strong|em)></\1>", "", out)
    # finitions sur le texte rendu (hors balises), y compris à cheval sur une balise
    out = re.sub(r"\.\.\.(?![^<]*>)", "…", out)
    out = re.sub(r"\.((?:</?(?:strong|em)>)+)\.\.", r"\1…", out)
    out = re.sub(r"\.\.((?:</?(?:strong|em)>)+)\.", r"\1…", out)
    out = re.sub(r"\u00a0((?:<[^>]+>)*)[ \u00a0]+", NB + r"\1", out)
    out = re.sub(r"[ ]+((?:<[^>]+>)*)\u00a0", r"\1" + NB, out)
    out = re.sub(r"\u00a0{2,}", NB, out)
    return out
