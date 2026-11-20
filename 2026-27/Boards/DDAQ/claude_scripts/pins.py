import xml.etree.ElementTree as ET, collections, sys
r=ET.parse('ddaq.xml').getroot()
pin=collections.defaultdict(dict); netnodes={}
for n in r.find('nets'):
    nm=n.get('name'); nodes=[]
    for x in n:
        pin[x.get('ref')][x.get('pin')]=(x.get('pinfunction') or '',nm); nodes.append(x.get('ref')+'.'+x.get('pin'))
    netnodes[nm]=nodes
refs=sys.argv[1].split(',')
for ref in refs:
    print('==',ref)
    for p,(f,nm) in sorted(pin[ref].items(), key=lambda t:(len(t[0]),t[0])):
        if nm.startswith('unconnected') and ref=='U1': continue
        print(f'  {p:>4} {f:<14} {nm}  {"" if nm in("GND","+3.3V","+5V") else netnodes[nm]}')
