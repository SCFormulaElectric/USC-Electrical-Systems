"""Update three brake calibration parts while preserving the edited layout."""
from pathlib import Path
import collections,copy,csv,hashlib,json,re,runpy,shutil,xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[1]
helpers=runpy.run_path(str(ROOT/'tools/convert_gnd_labels.py'))
children,form,tag=map(helpers.get,['children','form','tag'])
TOKEN=helpers['TOKENS']
q=lambda x:json.dumps(x,ensure_ascii=False)
def properties(v):
    out={}
    for _,_,p in children(v):
        m=re.match(r'\(property\s+("(?:\\.|[^"\\])*")\s+("(?:\\.|[^"\\])*")',p)
        if m:out[json.loads(m[1])]=json.loads(m[2])
    return out
def set_properties(v,fields):
    for name,value in fields.items():
        pattern=r'(\(property\s+'+re.escape(q(name))+r'\s+)("(?:\\.|[^"\\])*")'
        v,n=re.subn(pattern,lambda m:m[1]+q(value),v,count=1)
        if not n and name in ['Value','LCSC','LCSC Part #','MPN','Manufacturer']:
            raise ValueError('Missing required property '+name)
    return v
def edits(s,changes):
    for a,b,v in sorted(changes,reverse=True):s=s[:a]+v+s[b:]
    return s

PARTS={
 'R18':dict(value='270k 1%',mpn='0805W8F2703T5E',lcsc='C17589',manufacturer='UNI-ROYAL',sourcing_key='R_270k',
            note='AiM X05PSA02000P18: nominal low-fault boundary 0.357V raw; valid nominal zero-pressure output 0.5V.'),
 'R20':dict(value='11.3k 1%',mpn='SCR0805F11K3',lcsc='C3016737',manufacturer='VO',sourcing_key='R_11k3',
            note='AiM X05PSA02000P18: nominal high-fault boundary 4.695V raw; nominal full-scale output 4.5V.'),
 'R22':dict(value='47k 0.1%',mpn='RT0805BRD0747KL',lcsc='C865515',manufacturer='YAGEO',sourcing_key='R_47k_01',
            note='Bench calibration: hard-brake rising trip ~1.766V raw including hysteresis and divider loading. User measured ~1.8V hard brake; repeated vehicle validation pending.')}
for p in PARTS.values():
    p['source_url']='https://www.lcsc.com/product-detail/'+p['lcsc']+'.html'
    p['datasheet']=''
PARTS['R22']['datasheet']='https://www.yageogroup.com/component-documentation/download/specsheet/RT0805BRD0747KL'

before=ROOT/'before';before.mkdir(exist_ok=True)
for p in (ROOT/'revised').iterdir():
    if p.is_file() and (p.suffix in ['.kicad_sch','.kicad_pcb','.kicad_pro','.kicad_sym'] or p.name=='sym-lib-table'):
        shutil.copy2(p,before/p.name)

sch_path=ROOT/'revised/BSPD_2027.kicad_sch'
sch=sch_path.read_text();changes=[]
for a,b,v in children(sch):
    if tag(v)=='symbol':
        ref=properties(v).get('Reference')
        if ref in PARTS:
            p=PARTS[ref]
            fields={'Value':p['value'],'LCSC':p['lcsc'],'LCSC Part #':p['lcsc'],'MPN':p['mpn'],
                    'Manufacturer':p['manufacturer'],'Source URL':p['source_url'],
                    'Datasheet':p['datasheet'],'Design Notes':p['note']}
            changes.append((a,b,set_properties(v,fields)))
    elif tag(v)=='text' and 'X05SNP13520' in v:
        toks=list(TOKEN.finditer(v));text='AiM X05PSA02000P18: 0-2000psi / 0.5-4.5V; supply 8-16V. Brake trip ~1.76V raw; bench calibration pending.'
        v=v[:toks[2].start()]+q(text)+v[toks[2].end():];changes.append((a,b,v))
sch_path.write_text(edits(sch,changes))

# Reconcile PCB net names and symbol links with the user's readable schematic.
# Net partitions must be identical before any name is changed.
xml=ET.parse(ROOT/'reports/before_brake_sensor_update.xml').getroot()
node_net={(n.get('ref'),n.get('pin')):net.get('name') for net in xml.find('nets') for n in net.findall('node')}
components={c.get('ref'):c for c in xml.find('components')}
pcb_path=ROOT/'revised/BSPD_2027.kicad_pcb';pcb=pcb_path.read_text();changes=[];net_names=collections.defaultdict(set)
for a,b,v in children(pcb):
    if tag(v)!='footprint':continue
    ref=properties(v).get('Reference')
    if ref not in components:raise ValueError('Unexpected PCB footprint '+str(ref))
    for _,_,pad in children(v):
        if tag(pad)!='pad':continue
        num=json.loads(list(TOKEN.finditer(pad))[2].group())
        pn=form(pad,'net')
        if pn and (ref,num) in node_net:
            old=json.loads(list(TOKEN.finditer(pn))[-2].group());net_names[old].add(node_net[(ref,num)])
    ids=components[ref].findtext('tstamps')
    path=form(v,'path')
    if path:
        old=json.loads(list(TOKEN.finditer(path))[2].group());new=old.rsplit('/',1)[0]+'/'+ids
        v=v.replace(path,'(path '+q(new)+')',1)
    if ref in PARTS:
        p=PARTS[ref]
        v=set_properties(v,{'Value':p['value'],'LCSC':p['lcsc'],'LCSC Part #':p['lcsc'],
            'MPN':p['mpn'],'Manufacturer':p['manufacturer'],'SourceURL':p['source_url'],
            'Source URL':p['source_url'],'Datasheet':p['datasheet'],'Design Notes':p['note']})
    changes.append((a,b,v))
assert all(len(v)==1 for v in net_names.values()),'PCB and schematic differ electrically'
mapping={k:next(iter(v)) for k,v in net_names.items()}
assert len(set(mapping.values()))==len(mapping),'PCB net partitions differ'
pcb=edits(pcb,changes)
pcb=re.sub(r'(\(net\s+)("(?:\\.|[^"\\])*")',lambda m:m[1]+q(mapping.get(json.loads(m[2]),json.loads(m[2]))),pcb)
pcb_path.write_text(pcb)

spec=json.loads((ROOT/'circuit_spec.json').read_text())
for p in spec['parts']:
    if p['ref'] in PARTS:p.update(PARTS[p['ref']])
spec['brake_sensor']={'model':'AiM X05PSA02000P18','range_psi':[0,2000],'output_V':[0.5,4.5],
 'supply_V':[8,16],'user_measured_rest_raw_V':0.52,'user_measured_hard_brake_raw_V':1.8,
 'calibration_status':'BENCH_STARTING_POINT_VEHICLE_VALIDATION_PENDING','evidence':'User supplied IMG_5184.HEIC, November 3 2026'}
(ROOT/'circuit_spec.json').write_text(json.dumps(spec,indent=2)+'\n')
catalog=json.loads((ROOT/'reports/catalog.json').read_text())
for p in PARTS.values():
    catalog[p['sourcing_key']]={k:p[k] for k in ['mpn','lcsc','manufacturer','source_url','datasheet']}
    catalog[p['sourcing_key']].update(package='0805',footprint='Resistor_SMD:R_0805_2012Metric',
        description=p['value']+',125mW',verified_date='2026-11-04',notes='MPN/value/LCSC verified from official distributor page. Assembly inventory must be checked at ordering.')
(ROOT/'reports/catalog.json').write_text(json.dumps(catalog,indent=2)+'\n')

gen=ROOT/'generate_design.py';s=gen.read_text()
s=s.replace("r('brake_low_top','115k 1%'","r('brake_low_top','270k 1%'")
s=s.replace("r('brake_high_top','8.66k 1%'","r('brake_high_top','11.3k 1%'")
s=s.replace("r('brake_set_top','40.2k 0.1%'","r('brake_set_top','47k 0.1%'")
s=s.replace("'100k 1%':'R_100k'","'270k 1%':'R_270k','100k 1%':'R_100k'")
s=s.replace('Bench placeholder only (~35bar). AiM X05SNP13520 is confirmed; hard-brake pressure remains unconfirmed.',PARTS['R22']['note'])
s=s.replace('AiM X05SNP13520: 0–135 bar / 1–5 V. Hard-brake pressure remains unconfirmed. Resistor population requires vehicle calibration.',
 'AiM X05PSA02000P18: 0-2000psi / 0.5-4.5V, supply 8-16V. Brake trip ~1.76V raw; vehicle validation pending.')
gen.write_text(s)
report={'date':'2026-11-04','updated_parts':PARTS,'net_names_synchronized':{k:v for k,v in mapping.items() if k!=v},
 'schematic_placement_preserved':True,'pcb_geometry_untouched_by_metadata_update':True,'external_relayboard_latch':True}
(ROOT/'reports/brake_sensor_update.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'updated_parts':{k:v['value']+' / '+v['lcsc'] for k,v in PARTS.items()},'net_renames':report['net_names_synchronized']},indent=2))
