import re,html,glob,json,sys
SRC={2013:'bilan-notre-top-album',2014:'top-10-2014','2014-ep':'top-10-epsmixtapes-redaction',2015:'les-albums-qui-nous-ont-marques-en-2015',2016:'nos-projets-preferes-2016',2017:'top-projets-2017',2018:'top-projets-2018',2020:'rap-francais-top-2020-lref',2021:'top-projets-rap-francais-2021',2022:'top-projets-2022-le-meilleur-du-rap-francais'}
def clean(s):
    s=re.sub(r'<(?!/?(em|strong|i|b)\b)[^>]+>','',s)
    s=re.sub(r'<(/?)(i)>',r'<\1em>',s); s=re.sub(r'<(/?)b>',r'<\1strong>',s)
    s=html.unescape(s).replace('\xa0',' ')
    s=re.sub(r'\s+',' ',s).strip()
    s=re.sub(r'<(em|strong)>\s*</\1>','',s)
    return html.escape(html.unescape(re.sub('<[^>]+>','\x00',s))) if False else s
def txt(s): return re.sub(r'\s+',' ',html.unescape(re.sub('<[^>]+>','',s))).replace('\xa0',' ').strip()
out={}
for y,d in SRC.items():
    t=open(glob.glob(d+'/*.html')[0]).read()
    meta=dict(slug=d,title=txt(re.search(r'<h1[^>]*>(.*?)</h1>',t,re.S).group(1)),date=txt(re.search(r'<time[^>]*>(.*?)</time>',t,re.S).group(1)))
    a=re.search(r'Par\s*(?:<[^>]+>)*\s*([^<,]+?)\s*(?:</a>)?\s*,\s*le',t); meta['author']=a.group(1).strip() if a else ''
    p=t[t.find('<div class="prose">')+19:]; p=p[:p.find('Dans la même rubrique')]
    p=re.sub(r'<h2>\s*<div>Pages.*?</h2>','',p,flags=re.S); p=p.replace('<hr class="page-break"/>','')
    p=re.sub(r'Pages :.*','',p,flags=re.S) if y==2013 else p
    parts=re.split(r'<(h[1-4])[^>]*>(.*?)</\1>',p,flags=re.S)
    intro=[clean(x) for x in re.findall(r'<p[^>]*>(.*?)</p>',parts[0],re.S) if txt(x)]
    if y=='2014-ep':
        intro=[clean(parts[2])]
    items=[]
    i=1
    while i+2<len(parts):
        h=txt(parts[i+1]); body=parts[i+2]; i+=3
        if y=='2014-ep' and h.startswith('Parce que'): continue
        imgs=re.findall(r'<img[^>]+src="([^"]+)"',body)
        paras=[]
        for m in re.finditer(r'<(p|blockquote)[^>]*>(.*?)</\1>',body,re.S):
            c=clean(m.group(2))
            if not txt(c) or re.match(r'(Lire aussi|Ecouter|Écouter)',txt(c)): continue
            paras.append(('> ' if m.group(1)=='blockquote' else '')+c)
        items.append(dict(head=h,img=imgs[0] if imgs else '',paras=paras))
    meta['intro']=intro; meta['items']=items; meta['cover']=(re.search(r'<figure class="cover"><img src="([^"]+)"',t) or [None,''])[1]
    out[str(y)]=meta
json.dump(out,open(sys.argv[1],'w'),ensure_ascii=False,indent=1)
for y,m in out.items(): print(y,m['author'],len(m['items']),[ (x['head'][:40],len(x['paras']),bool(x['img'])) for x in m['items']][:15])
