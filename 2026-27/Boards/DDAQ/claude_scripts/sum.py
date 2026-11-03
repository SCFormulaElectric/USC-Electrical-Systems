import json, collections
e=json.load(open('erc.json',encoding='utf-8'))
c=collections.Counter(); ex=collections.defaultdict(list)
for s in e['sheets']:
    for v in s['violations']:
        c[(v['type'],v['severity'])]+=1
        ex[v['type']].append('; '.join(i['description'] for i in v['items'])[:150])
print('ERC'); 
for k,n in c.most_common(): print(n,k, '|', ex[k[0]][0])
for t in ('pin_not_driven','power_pin_not_driven','pin_to_pin','label_dangling','different_unit_net','multiple_net_names','lib_symbol_issues','lib_symbol_mismatch','footprint_link_issues'):
    if t in ex: print('--',t); [print('   ',x) for x in ex[t][:12]]
d=json.load(open('drc.json',encoding='utf-8'))
for sec in ('violations','unconnected_items','schematic_parity'):
    cc=collections.Counter(v['type'] for v in d.get(sec,[]))
    print('DRC',sec,len(d.get(sec,[])),dict(cc))
for v in d.get('schematic_parity',[]): print('   P', v['description'][:60],'|','; '.join(i['description'] for i in v['items'])[:120])
nets=collections.Counter()
for v in d.get('unconnected_items',[]):
    import re
    m=re.search(r'\[([^\]]+)\]',v['items'][0]['description']); nets[m.group(1) if m else '?']+=1
print('   unconnected by net',dict(nets))
