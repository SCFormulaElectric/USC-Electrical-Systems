from sch import *
import json,re,collections
root=load('backup_DDAQ.kicad_sch.orig')
R=lambda v:round(float(v),2)
wires=[]; labels=[]; syms=[]; ncs=[]; juncs=[]
for c in root:
    if not isinstance(c,list): continue
    if c[0]=='wire':
        pts=[(R(p[1]),R(p[2])) for p in one(c,'pts')[1:]]; wires.append((pts,one(c,'uuid')[1]))
    elif c[0] in('label','global_label','hierarchical_label'):
        a=one(c,'at'); labels.append((c[0],c[1],(R(a[1]),R(a[2])),one(c,'uuid')[1]))
    elif c[0]=='no_connect':
        a=one(c,'at'); ncs.append((R(a[1]),R(a[2])))
    elif c[0]=='symbol':
        lid=one(c,'lib_id')[1]; a=one(c,'at')
        props={p[1]:p[2] for p in find(c,'property')}
        syms.append((props.get('Reference'),lid,(R(a[1]),R(a[2]))))
print('counts wires',len(wires),'labels',len(labels),'syms',len(syms))
pinpos=json.load(open('pins.json'))
# build adjacency graph of points via wires
def at_point(pt):
    out=[]
    for l in labels:
        if l[2]==pt: out.append(f'{l[0][0]}:{l[1]}')
    for s in syms:
        if s[0] and s[0].startswith('#') and s[2]==pt: out.append('PWR:'+s[1].split(':')[1])
    if pt in ncs: out.append('NC')
    return out
for ref,pins in pinpos.items():
    print('==',ref)
    for pn,(name,pt) in pins.items():
        pt=tuple(pt); direct=at_point(pt)
        ws=[w for w in wires if pt in w[0]]
        far=[]
        for w in ws:
            o=[p for p in w[0] if p!=pt][0]; far.append((o,at_point(o), sum(1 for w2 in wires if o in w2[0])))
        if direct or ws: print(f'  {pn:>3} {name:<16} direct={direct} wires={[(f[0],f[1],f[2]) for f in far]}')
