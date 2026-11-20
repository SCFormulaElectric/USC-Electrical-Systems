import xml.etree.ElementTree as ET, json, collections, re, sys
r=ET.parse('ddaq.xml').getroot()
comps=[]
for c in r.find('components'):
    ref=c.get('ref'); val=c.findtext('value'); fp=c.findtext('footprint') or ''
    lib=c.find('libsource'); lid=(lib.get('lib')+':'+lib.get('part')) if lib is not None else ''
    comps.append((ref,val,fp,lid))
def key(r):
    m=re.match(r'([A-Za-z#]+)(\d+)',r[0]); return (m.group(1),int(m.group(2))) if m else (r[0],0)
comps.sort(key=key)
# group passives by prefix+value
non=[c for c in comps if not re.match(r'^(R|C|D|FB|F)\d',c[0])]
for c in non: print(c)
print('---- passive groups')
g=collections.defaultdict(list)
for c in comps:
    if re.match(r'^(R|C|D|FB|F)\d',c[0]): g[(re.match(r'[A-Z]+',c[0]).group(),c[1])].append(c[0])
for k,v in sorted(g.items()): print(k,len(v),v[0],'..',v[-1])
print('---- nets')
nets=r.find('nets')
names=[]
for n in nets:
    nm=n.get('name'); nodes=[(x.get('ref'),x.get('pin'),x.get('pinfunction')) for x in n]
    names.append((nm,len(nodes)))
print(len(names))
print(', '.join(f'{a}({b})' for a,b in names if not a.startswith('Net-(') and not a.startswith('unconnected')))
print('unnamed nets', sum(1 for a,b in names if a.startswith('Net-(')), 'unconnected', sum(1 for a,b in names if a.startswith('unconnected')))
