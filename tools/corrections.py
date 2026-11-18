"""Corrections orthographiques et typographiques appliquées à la génération du site.
Les données brutes (data/lerapenfrance-archive.json) ne sont jamais modifiées.
"""
import re
from collections import Counter
from bs4 import NavigableString, Comment

# Fautes d'orthographe relevées dans le corpus et validées à la main (mot fautif -> correction).
# Les mots valides en anglais (presence, region, detail…) sont exclus pour ne pas abîmer des citations.
MOTS = {
    "avecc": "avec", "beaucoupn": "beaucoup", "uelques": "quelques", "gtrand": "grand", "ertains": "certains",
    "musciale": "musicale", "propr": "propre", "collectig": "collectif", "prodcution": "production",
    "inalement": "finalement", "quatres": "quatre", "medias": "médias", "periode": "période", "pourqui": "pourquoi",
    "troisème": "troisième", "nouveuax": "nouveaux", "umière": "lumière", "cinqs": "cinq", "sûement": "sûrement",
    "acompagné": "accompagné", "liberte": "liberté", "réfléxion": "réflexion", "conaissait": "connaissait",
    "malheuresement": "malheureusement", "aprécie": "apprécie", "décidement": "décidément",
    "décidémment": "décidément", "cloture": "clôture", "cloturer": "clôturer", "introdiction": "introduction",
    "ncarne": "incarne", "selectionné": "sélectionné", "sympatique": "sympathique", "résonnance": "résonance",
    "ouffrance": "souffrance", "interprête": "interprète", "quizaine": "quinzaine", "réveler": "révéler",
    "fonsdé": "fondé", "interprêter": "interpréter", "intéréssés": "intéressés", "recomander": "recommander",
    "mbitieux": "ambitieux", "icone": "icône", "sustances": "substances", "emblerait": "semblerait",
    "perpetuelle": "perpétuelle", "clôre": "clore", "wisky": "whisky", "intrsus": "intrus", "syndrôme": "syndrome",
    "éritier": "héritier", "lointainte": "lointaine", "naiveté": "naïveté", "permanant": "permanent",
    "prédecesseur": "prédécesseur", "plendeur": "splendeur", "préferer": "préférer", "éléctions": "élections",
    "floppée": "flopée", "acceuillant": "accueillant", "passionante": "passionnante", "terasse": "terrasse",
    "aperçevoir": "apercevoir", "extrordinaires": "extraordinaires", "hierarchie": "hiérarchie",
    "buldozer": "bulldozer", "fantome": "fantôme", "recreer": "recréer", "dilemne": "dilemme",
    "interprêtée": "interprétée", "voisinnage": "voisinage", "semplé": "semblé", "surement": "sûrement",
    "celà": "cela", "québecois": "québécois", "ré-écrire": "réécrire",
}
_MOTS_RE = re.compile(r"(?<![\w’'-])(" + "|".join(sorted(map(re.escape, MOTS), key=len, reverse=True)) + r")(?![\w’'-])", re.I)

# Fautes de grammaire repérables sans ambiguïté.
PHRASES = [
    (r"\bil y à\b", "il y a"),
    (r"\b(qui|ça|on|il|elle) à (fait|été|eu|pris|marché|grave|su|dit|vu|réussi|toujours|jamais)\b", r"\1 a \2"),
    (r"\bà été\b", "a été"),
    (r"\bgrâce a\b", "grâce à"),
    (r"\bjusqu['’]a\b", "jusqu’à"),
    (r"\bquelques temps\b(?! (forts|morts))", "quelque temps"),
    (r"\bc['’]est à dire\b", "c’est-à-dire"),
    (r"\bvoir même\b", "voire même"),
    (r"\bdès fois\b", "des fois"),
    (r"\btous le monde\b", "tout le monde"),
    (r"\bça va de soit\b", "ça va de soi"),
    (r"(?<!du )(?<!après )\btout les (?=(deux|trois|quatre|cinq|six|sept|huit|dix|ingrédients|artistes|quartiers|domaines|égards|évènements|événements|jours|soirs|ans|mois|week-ends|sons|morceaux|titres|albums|projets|rappeurs|médias|genres|styles|niveaux|points|thèmes|membres)\b)", "tous les "),
    (r"\bneufs (lieux|titres|morceaux|ans)\b", r"neuf \1"),
    (r"\ble fameux quarter\b", "le fameux quartier"),
]
PHRASES = [(re.compile(p), r) for p, r in PHRASES]

NNBSP, NBSP = " ", " "


def _case(src, dst):
    return dst[0].upper() + dst[1:] if src[:1].isupper() else dst


def corrige_texte(t, stats, debut_de_noeud=False):
    o = t
    t = _MOTS_RE.sub(lambda m: (stats.update(["orthographe"]), _case(m.group(1), MOTS[m.group(1).lower()]))[1], t)
    for rx, rep in PHRASES:
        t, n = rx.subn(rep, t)
        if n:
            stats["grammaire"] += n
    # typographie
    t2 = re.sub(r"[ \t]{2,}", " ", t)
    t2 = re.sub(r"[ \t  ]+,", ",", t2)
    t2 = re.sub(r"\.\.\.", "…", t2)
    t2 = re.sub(r"(?<=[^\W_])'(?=[^\W\d_])", "’", t2)
    t2 = re.sub(r"(?<=[^\s«(\[“/=&?!])[ \t\u00a0\u202f]*([;!?]+)(?=[\s»”)\]….]|$)", NNBSP + r"\1", t2)
    t2 = re.sub(r"(?<=[^\s\W_])[ \t  ]*:(?=\s|$)", NBSP + ":", t2)
    t2 = re.sub(r"^[ \t ]+([;!?])", NNBSP + r"\1", t2) if debut_de_noeud else t2
    t2 = re.sub(r"«[ \t  ]*", "«" + NBSP, t2)
    t2 = re.sub(r"[ \t  ]*»", NBSP + "»", t2)
    if t2 != t:
        stats["typographie"] += 1
    return t2


def corrige_html(soup, stats):
    for node in list(soup.find_all(string=True)):
        if isinstance(node, Comment) or node.parent.name in ("script", "style", "code", "pre"):
            continue
        prev = node.previous_sibling
        new = corrige_texte(str(node), stats, debut_de_noeud=prev is not None)
        if new != str(node):
            node.replace_with(NavigableString(new))
    return soup


EN = set("the and of to your you is are for with that this it be can as on or by from have will".split())
FR = set("le la les de des et un une est pour dans que qui sur avec pas il elle ce sont au du".split())


def est_spam(texte):
    """Vrai si le texte est un contenu en anglais injecté (piratage) et non un article en français."""
    w = re.findall(r"[a-zàâçéèêëîïôûùüœ]+", texte.lower())
    if len(w) < 40:
        return False
    en = sum(x in EN for x in w)
    fr = sum(x in FR for x in w)
    return en > fr * 0.6 and en / len(w) > 0.08


SPAM_KW = re.compile(r"\b(replica|rolex|casino|viagra|cialis|loans?|essays?|jerseys|cheap|pills|dating|betting|crypto|forex|"
                     r"backlinks?|supplements?|meticore|biofit|weight loss|keto|wholesale|escort|bitcoin|payday|insurance|"
                     r"recommended websites?|healthy eating|nutrients)\b", re.I)


def retire_paragraphes_spam(soup):
    """Supprime les paragraphes publicitaires en anglais injectés lors du piratage. Renvoie le nombre retiré."""
    n = 0
    for el in soup.find_all(["p", "div", "h2", "h3", "h4", "li"]):
        if el.find(["p", "div"]):
            continue
        t = el.get_text(" ", strip=True)
        w = re.findall(r"[a-z]+", t.lower())
        if len(w) >= 12 and SPAM_KW.search(t) and sum(x in EN for x in w) / len(w) > 0.08:
            el.decompose()
            n += 1
    return n
