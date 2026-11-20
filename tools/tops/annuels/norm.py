import json,re
d=json.load(open('raw.json'))
Y2013=[('Rocé','Gunz N’ Rocé'),('Kaaris','Or Noir'),('Gaël Faye','Pili-Pili sur un croissant au beurre'),('Aelpeacha & A2H','Studio Liqueur'),('Casseurs Flowters','Orelsan et Gringe sont les Casseurs Flowters'),('C.Sen','Le Tunnel'),('Le Gouffre','Marche Arrière'),('Lomepal','Cette foutue perle'),('Lucio Bukowski & Tcheep','De la survie des fauves en terre moderne'),('Anton Serra','Frandjos')]
out=[]
for y,m in d.items():
    items=[]
    for x in m['items']:
        x['paras']=[p for p in x['paras'] if not p.startswith('Article publié')]
        if not x['head']:
            if items: items[-1]['paras']+=x['paras']
            continue
        items.append(x)
    res=[]
    for i,x in enumerate(items):
        h=x['head'].replace(' (ICI)','')
        if y=='2013':
            a,al=Y2013[i]; r=None; tag=x['head']
        else:
            mm=re.match(r'(\d+)\s*[–.\-)]\s*(.+?)\s+–\s+(.+)$',h)
            r=int(mm.group(1)); a,al=mm.group(2).strip(),mm.group(3).strip(); tag=''
            if y=='2014-ep' or (y=='2022' and r==8): a,al=al,a
        al=al.replace('(partie 1 & partie 2','(parties 1 & 2)').replace('))',')')
        res.append(dict(rank=r,artist=a,album=al,tag=tag,img=x['img'],paras=x['paras']))
    m['items']=res; m['key']=y
    out.append(m)
W='https://web.archive.org/web/2020im_/http://lerapenfrance.fr/wp-content/uploads/2014/01/'
I13=['gunz-n-roce.jpg','kaaris-or-noir.jpg','cover-alb-gael-faye-hd.jpg','906582_535790663139404_1563521320_o.jpg','ayld8whq4kjx0o36gtp9hedso.1000x1000x1.jpg','c-sen-le-tunnel-CD-tt-width-360-height-342-attachment_id-339817-crop-1.jpg','1236559_10151793945445270_1258545287_n.jpg','560856_581638431880076_441770219_n.jpg','a0639383416_10.jpg','image226.jpg']
for x,f in zip(out[0]['items'],I13): x['img']=W+f
json.dump(out,open('years.json','w'),ensure_ascii=False,indent=1)
for m in out: print(m['key'],[(x['rank'],x['artist'],x['album']) for x in m['items']])
