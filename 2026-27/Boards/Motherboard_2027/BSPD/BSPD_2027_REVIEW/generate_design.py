"""Generate the editable review schematic and a physical component/net manifest.

All package pin numbers are physical pins. PCB and schematic consume one manifest.
Release is conditional on the vehicle measurements recorded in DESIGN_REVIEW.md.
"""
import json, uuid, re, pathlib, csv

ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT / 'revised'
OUT.mkdir(exist_ok=True)
uid = lambda: str(uuid.uuid4())
sheet_id = '7f94e731-ab98-4d5a-af18-a20be0072027'
parts=[]
counters={}
previous_spec=json.loads((ROOT/'circuit_spec.json').read_text()) if (ROOT/'circuit_spec.json').exists() else {'parts':[]}
previous_refs={p['role']:p['ref'] for p in previous_spec['parts']}

def add(kind, role, value, footprint, pins, x, y, mpn='', lcsc='', note='', pcb=None):
    prefix={'R':'R','C':'C','D':'D','DZ':'D','F':'F','J':'J','IC':'U','NPN':'Q','PNP':'Q','NFET':'Q','REF':'U','LDO':'U','SUP':'U'}[kind]
    counters[prefix]=counters.get(prefix,0)+1
    reference=previous_refs.get(role,f'{prefix}{counters[prefix]}')
    counters[prefix]=max(counters[prefix],int(reference[len(prefix):]))
    p=dict(ref=reference,kind=kind,role=role,value=value,footprint=footprint,
           pins={str(k):v for k,v in pins.items()},x=round(x/1.27)*1.27,y=round(y/1.27)*1.27,mpn=mpn,lcsc=lcsc,note=note,uuid=str(uuid.uuid5(uuid.UUID(sheet_id),role)),pcb=pcb)
    parts.append(p)
    return p['ref']

RFP='Resistor_SMD:R_0805_2012Metric'
CFP='Capacitor_SMD:C_0805_2012Metric'
SO14='Package_SO:SOIC-14_3.9x8.7mm_P1.27mm'
SOT='Package_TO_SOT_SMD:SOT-23'
def r(role,value,a,b,x,y,**kw): return add('R',role,value,RFP,{1:a,2:b},x,y,**kw)
def c(role,value,a,b,x,y,**kw): return add('C',role,value,CFP,{1:a,2:b},x,y,**kw)
def d(role,a,k,x,y,**kw): return add('D',role,'1N4148W-7-F','Diode_SMD:D_SOD-123',{1:k,2:a},x,y,mpn='1N4148W-7-F',lcsc='C83528',**kw)

# Connector: exact model, footprint, physical placement, and all six original nets retained.
add('J','vehicle_connector','043045-0612','Connector_Molex:Molex_Micro-Fit_3.0_43045-0612_2x03_P3.00mm_Vertical',
    {1:None,2:'BSPD_SIGNAL',3:'I_RAW',4:'B_RAW',5:'GND',6:'VIN'},55,70,mpn='430450612',lcsc='C234188',
    note='Pin 1 stays unused. Pin 2 is non-latching: HIGH healthy, LOW fault. The external relayboard retains trips and controls manual reset.',pcb=[149.6538,68.9186,90])

# Protected supply and separate reference/logic rails.
add('F','input_fuse','0451.250MRL','Fuse:Fuse_Littelfuse-NANO2-451_453',{1:'VIN',2:'VIN_F'},125,55,mpn='0451.250MRL',lcsc='C151116',
    note='Final interrupt rating must exceed GLV prospective short-circuit current.')
add('D','reverse_protection','SS14','Diode_SMD:D_SMA',{1:'VP',2:'VIN_F'},125,70,mpn='SS14',lcsc='C2480')
add('DZ','supply_tvs','SMBJ18A','Diode_SMD:D_SMB',{1:'VP',2:'GND'},125,85,mpn='SMBJ18A',lcsc='C151256')
add('C','input_bulk','10uF/50V','Capacitor_SMD:C_1206_3216Metric',{1:'VP',2:'GND'},125,100)
c('input_bypass','100nF/50V','VP','GND',125,115)
add('LDO','logic_supply','L78L05ABUTR','Package_TO_SOT_SMD:SOT-89-3',{1:'V5',2:'GND',3:'VP'},185,70,mpn='L78L05ABUTR',lcsc='C42738')
c('logic_bulk','1uF/25V','V5','GND',185,100)
c('logic_bypass','100nF/50V','V5','GND',185,115)
r('clamp_rail_bleed','1k 1%','V5','GND',185,130,note='Provides sink load for clamp current; regulator itself cannot sink current.')
r('reference_bias','3.3k 1%','VP','REF5',185,145)
add('REF','precision_reference','LM4040AIM3-5.0/NOPB',SOT,{1:'REF5',2:'GND',3:'GND'},125,145,mpn='LM4040AIM3-5.0/NOPB',lcsc='C140239')
c('reference_bypass','100nF/50V','REF5','GND',125,165)
add('SUP','power_supervisor','MCP809T-450I/TT',SOT,{1:'GND',2:'POR_N',3:'V5'},55,135,mpn='MCP809T-450I/TT',lcsc='C511285')
c('supervisor_bypass','100nF/50V','V5','GND',55,165)

# Current comparators: LM2901B pins from the TI quad-comparator pinout.
# A: sense below window -> FAULT_OK low. B: above window -> low.
# C: high-current -> released HIGH. D: protected 12V undervoltage -> low.
add('IC','current_and_uv_comparators','LM2901BIDR',SO14,
    {1:'FAULT_OK',2:'FAULT_OK',3:'VP',4:'I_LOW',5:'I_SENSE',6:'I_SENSE',7:'I_HIGH',8:'I_THRESH',9:'I_CMP',10:'REF_HALF',11:'VIN_DIV',12:'GND',13:'FAULT_OK',14:'C_HIGH'},285,75,mpn='LM2901BIDR',lcsc='C22427890')
c('current_ic_bypass','100nF/50V','VP','GND',245,115)
r('current_series','10k 0.1%','I_RAW','I_SENSE',245,135)
r('current_open_bias','10k 0.1%','I_SENSE','GND',285,135)
c('current_filter','10nF/50V','I_SENSE','GND',325,135)
add('IC','current_input_clamp','BAT54S,215',SOT,{1:'GND',2:'V5',3:'I_SENSE'},325,160,mpn='BAT54S,215',lcsc='C47546')
r('current_low_top','1M 1%','REF5','I_LOW',245,180,note='Nominal raw low limit ~0.099V permits normal DHAB low clamping at a qualified sensor supply.')
r('current_low_bottom','10k 0.1%','I_LOW','GND',285,180)
r('current_high_top','10k 0.1%','REF5','I_HIGH',245,195,note='Nominal raw high limit ~4.88V permits DHAB nominal high clamping; sensor-supply extremes still require reference qualification.')
r('current_high_bottom','9.53k 0.1%','I_HIGH','GND',285,195)
r('current_set_top','28k 0.1%','REF5','I_THRESH',245,215,note='Channel 2 calibration part; not a final vehicle threshold until sensor supply and errors are measured.')
r('current_set_bottom','10k 0.1%','I_THRESH','GND',285,215,note='Change soldered resistor values to calibrate; no moving contacts.')
r('current_hysteresis_input','1k 1%','I_SENSE','I_CMP',325,215)
r('current_hysteresis_feedback','4.7M 1%','C_HIGH','I_CMP',325,195)
r('current_pullup','10k 1%','V5','C_HIGH',325,180)
r('undervoltage_top','33k 1%','VP','VIN_DIV',245,235,note='Conservative 12V-class undervoltage cutoff also protects AiM 10V minimum supply. Qualify actual GLV range.')
r('undervoltage_bottom','10k 0.1%','VIN_DIV','GND',285,235)

# Brake window + hard-braking comparison + continuous-coincidence timer comparator.
add('IC','brake_and_timer_comparators','LM2901BIDR',SO14,
    {1:'FAULT_OK',2:'FAULT_OK',3:'VP',4:'B_LOW',5:'B_SENSE',6:'B_SENSE',7:'B_HIGH',8:'B_THRESH',9:'B_CMP',10:'TIMER',11:'REF_HALF',12:'GND',13:'FAULT_OK',14:'B_HARD'},465,75,mpn='LM2901BIDR',lcsc='C22427890')
c('brake_ic_bypass','100nF/50V','VP','GND',425,115)
r('brake_series','10k 0.1%','B_RAW','B_SENSE',425,135)
r('brake_open_bias','10k 0.1%','B_SENSE','GND',465,135)
c('brake_filter','10nF/50V','B_SENSE','GND',505,135)
add('IC','brake_input_clamp','BAT54S,215',SOT,{1:'GND',2:'V5',3:'B_SENSE'},505,160,mpn='BAT54S,215',lcsc='C47546')
r('brake_low_top','115k 1%','REF5','B_LOW',425,180)
r('brake_low_bottom','10k 1%','B_LOW','GND',465,180)
r('brake_high_top','8.66k 1%','REF5','B_HIGH',425,195)
r('brake_high_bottom','10k 1%','B_HIGH','GND',465,195)
r('brake_set_top','40.2k 0.1%','REF5','B_THRESH',425,215,note='Bench placeholder only (~35bar). AiM X05SNP13520 is confirmed; hard-brake pressure remains unconfirmed.')
r('brake_set_bottom','10k 0.1%','B_THRESH','GND',465,215,note='Change soldered resistors only after hydraulic calibration.')
r('brake_hysteresis_input','10k 1%','B_SENSE','B_CMP',505,215)
r('brake_hysteresis_feedback','2.2M 1%','B_HARD','B_CMP',505,195)
r('brake_pullup','10k 1%','V5','B_HARD',505,180)

# Timer: discharge whenever either high-current or hard-braking is absent.
add('IC','coincidence_logic','74HC132D,653',SO14,
    {1:'C_HIGH',2:'B_HARD',3:'DISCHARGE',4:'FAULT_OK',5:'POR_N',6:'PERMIT_N',7:'GND',8:'PERMIT',9:'PERMIT_N',10:'PERMIT_N',11:None,12:'GND',13:'GND',14:'V5'},65,250,mpn='74HC132D,653',
    note='Gate 1 controls coincidence timing. Gates 2/3 buffer PERMIT=FAULT_OK AND POR_N; no fault memory is present.')
c('nand_bypass','100nF/50V','V5','GND',65,290)
r('timer_charge','39k 1%','REF5','TIMER',245,270)
c('timer_cap','10uF/25V X7R 10%','TIMER','GND',285,270,
    note='Timer is conservatively early: nominal ~270ms; capacitance positive tolerance/temp and reset-FET leakage must fit 500ms including external relay.')
r('timer_half_top','47k 0.1%','REF5','REF_HALF',245,295)
r('timer_half_bottom','47k 0.1%','REF_HALF','GND',285,295)
r('discharge_gate_series','470 1%','DISCHARGE','DIS_GATE',245,320)
r('discharge_gate_bias','100k 1%','DIS_GATE','GND',285,320)
add('NFET','timer_reset_fet','2N7002,215',SOT,{1:'DIS_GATE',2:'GND',3:'TIMER'},325,290,mpn='2N7002,215',lcsc='C65189')

# All fault memory belongs to the external relayboard. The fault bus drives
# CMOS inputs only; the two U8 gates source the transistor's base current.
r('fault_bus_pullup','10k 1%','V5','FAULT_OK',115,315)

# Source an active-high permit through a current-limiting output resistor.
# Unpowered/unhealthy state is pulled low; external relay/latch must drop out.
r('permit_base','10k 1%','PERMIT','N_BASE',425,265)
r('permit_base_bias','100k 1%','N_BASE','GND',465,265)
add('NPN','output_level_shift','MMBT3904,215',SOT,{1:'N_BASE',2:'GND',3:'N_COL'},425,290,mpn='MMBT3904,215',lcsc='C426835')
r('source_base_limit','47k 1%','N_COL','P_BASE',465,290)
r('source_base_off_bias','100k 1%','VP','P_BASE',505,290)
add('PNP','output_source','MMBT3906,215',SOT,{1:'P_BASE',2:'VP',3:'OUT_SRC'},465,325,mpn='MMBT3906,215',lcsc='C75549')
add('R','output_short_limit','2.2k 1%','Resistor_SMD:R_1206_3216Metric',{1:'OUT_SRC',2:'BSPD_SIGNAL'},425,350,
    note='Output load verified on motherboard: 24k divider. 1206 power rating required.')
r('output_default_low','47k 1%','BSPD_SIGNAL','GND',465,350)
add('DZ','output_clamp','BZT52C15-7-F','Diode_SMD:D_SOD-123',{1:'BSPD_SIGNAL',2:'GND'},505,350,mpn='BZT52C15-7-F',lcsc='C177014')

# Resolve every fitted component to the independently verified manufacturer
# catalog. Sourcing changes do not change stable role-based UUIDs.
catalog=json.loads((ROOT/'reports'/'catalog.json').read_text())
rkeys={'1k 1%':'R_1k','3.3k 1%':'R_3k3','10k 1%':'R_10k','10k 0.1%':'R_10k_01',
       '100k 1%':'R_100k','150k 1%':'R_150k','4.7k 1%':'R_4k7','11.3k 1%':'R_11k3',
       '28k 0.1%':'R_28k_01','9.53k 0.1%':'R_9k53_01','1M 1%':'R_1M','4.7M 1%':'R_4M7','26.1k 1%':'R_26k1','33k 1%':'R_33k','115k 1%':'R_115k',
       '8.66k 1%':'R_8k66','40.2k 0.1%':'R_40k2_01','2.2M 1%':'R_2M2','39k 1%':'R_39k',
       '47k 0.1%':'R_47k_01','470 1%':'R_470','47k 1%':'R_47k','2.2k 1%':'R_2k2_1206'}
ckeys={'100nF/50V':'decoupling_100n','10nF/50V':'filter_10n','1uF/25V':'bulk_1u',
       '10uF/50V':'input_bulk_10u','10uF/25V X7R 10%':'timer_10u_x7r'}
rolekeys={'coincidence_logic':'schmitt_nand','power_fault_or':'or_diode'}
for p in parts:
    if p['kind']=='R': key=rkeys[p['value']]
    elif p['kind']=='C': key=ckeys[p['value']]
    elif p['role'] in rolekeys: key=rolekeys[p['role']]
    else: key=next(k for k,v in catalog.items() if v['mpn']==p['mpn'])
    src=catalog[key]
    p.update(mpn=src['mpn'],lcsc=src['lcsc'],manufacturer=src['manufacturer'],
             datasheet=src.get('datasheet',''),source_url=src['source_url'],sourcing_key=key)
    if p['role']=='power_fault_or':p['value']=src['mpn']
    if p['role']=='logic_bulk':p['value']='1uF/50V'

# Use native passive drawings; custom IC symbols expose every physical pin.
class Q(str): pass
def parse(s):
    toks=re.findall(r'"(?:\\.|[^"\\])*"|[^\s()]+|[()]',s)
    def rec(i):
        vals=[]; i+=1
        while toks[i]!=')':
            if toks[i]=='(': v,i=rec(i); vals.append(v)
            else:
                t=toks[i]; vals.append(Q(json.loads(t)) if t.startswith('"') else t); i+=1
        return vals,i+1
    return rec(0)[0]
def emit(v):
    if isinstance(v,list): return '('+' '.join(emit(x) for x in v)+')'
    return json.dumps(str(v),ensure_ascii=False) if isinstance(v,Q) else str(v)
def native(name):
    lib=parse(pathlib.Path('/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols/Device.kicad_sym').read_text())
    sym=next(s for s in lib if isinstance(s,list) and s[:2]==['symbol',name])
    sym[1]=Q('Review:'+name)
    return sym
def pin_meta(p):
    kind=p['kind']; keys=list(p['pins'])
    if kind in ('R','C','D','DZ','F'): return {k:(-3.81 if k=='1' else 3.81,0,'passive',k,0 if k=='1' else 180) for k in keys}
    if kind=='J': return {k:(-12.7, (int(k)-3.5)*2.54,'passive',k,0) for k in keys}
    names={}
    outputs=set(); oc=set(); power=set(); powerout=set()
    if p['role'] in ('current_and_uv_comparators','brake_and_timer_comparators'):
        names={'1':'OUT1','2':'OUT2','3':'VCC','4':'IN1-','5':'IN1+','6':'IN2-','7':'IN2+','8':'IN3-','9':'IN3+','10':'IN4-','11':'IN4+','12':'GND','13':'OUT4','14':'OUT3'}
        oc={'1','2','13','14'}; power={'3','12'}
    elif p['role']=='coincidence_logic':
        names={str(k):v for k,v in enumerate(['1A','1B','1Y','2A','2B','2Y','GND','3Y','3A','3B','4Y','4A','4B','VCC'],1)}
        outputs={'3','6','8','11'}; power={'7','14'}
    elif kind=='SUP': names={'1':'GND','2':'RESET_N','3':'VDD'};outputs={'2'};power={'1','3'}
    elif kind=='LDO': names={'1':'OUT','2':'GND','3':'IN'};power={'2','3'};powerout={'1'}
    elif kind=='REF': names={'1':'K','2':'A','3':'A/NC'}
    elif kind in ('NPN','PNP'): names={'1':'B','2':'E','3':'C'}
    elif kind=='NFET': names={'1':'G','2':'S','3':'D'}
    elif p['role'].endswith('input_clamp'): names={'1':'A1','2':'K2','3':'K1/A2'}
    left=[k for k in keys if k not in outputs|oc|powerout]; right=[k for k in keys if k in outputs|oc|powerout]
    coords={}
    for arr,x,ang in [(left,-12.7,0),(right,12.7,180)]:
        for i,k in enumerate(arr):
            typ='open_collector' if k in oc else 'output' if k in outputs else 'power_out' if k in powerout else 'power_in' if k in power else 'passive' if kind in ('REF','NPN','PNP','NFET') or p['role'].endswith('input_clamp') else 'input'
            coords[k]=(x,(i-(len(arr)-1)/2)*2.54,typ,names.get(k,k),ang)
    return coords

def symid(p): return 'Review:'+({'R':'R','C':'C','D':'D','DZ':'D_Zener','F':'Fuse'}.get(p['kind'],p['role']))
libsyms={}
for p in parts:
    sid=symid(p)
    if sid in libsyms: continue
    if p['kind'] in ('R','C','D','DZ','F'):
        libsyms[sid]=native(sid.split(':')[-1]);continue
    meta=pin_meta(p);height=max(5.08,max(abs(t[1]) for t in meta.values())+1.27)
    libsyms[sid]=['symbol',Q(sid),['pin_names',['offset','0.508']],['in_bom','yes'],['on_board','yes'],
        ['property',Q('Reference'),Q(p['ref'][0]),['at','0',str(height+2.54),'0'],['effects',['font',['size','1.27','1.27']]]],
        ['property',Q('Value'),Q(p['value']),['at','0',str(-height-2.54),'0'],['effects',['font',['size','1.27','1.27']]]],
        ['symbol',Q(p['role']+'_0_1'),['rectangle',['start','-10.16',str(height)],['end','10.16',str(-height)],['stroke',['width','0.254'],['type','default']],['fill',['type','background']]]],
        ['symbol',Q(p['role']+'_1_1')]+[['pin',t[2],'line',['at',str(t[0]),str(-t[1]),str(t[4])],['length','2.54'],['name',Q(t[3]),['effects',['font',['size','1','1']]]],['number',Q(k),['effects',['font',['size','1','1']]]]] for k,t in meta.items()]]

libsyms['Review:PWR_FLAG']=['symbol',Q('Review:PWR_FLAG'),['in_bom','no'],['on_board','no'],
    ['property',Q('Reference'),Q('#FLG'),['at','0','0','0'],['effects',['font',['size','1.27','1.27']],'hide']],
    ['property',Q('Value'),Q('PWR_FLAG'),['at','0','0','0'],['effects',['font',['size','1.27','1.27']],'hide']],
    ['symbol',Q('PWR_FLAG_1_1'),['pin','power_out','line',['at','0','0','90'],['length','0'],['name',Q('pwr'),['effects',['font',['size','1','1']]]],['number',Q('1'),['effects',['font',['size','1','1']]]]]]]

def q(s): return json.dumps(str(s),ensure_ascii=False)
def prop(name,value,x,y,hide=False,angle=0):
    return f'(property {q(name)} {q(value)} (at {x} {y} {angle}) (effects (font (size 1.0 1.0))'+(' hide' if hide else '')+'))'

# Native passive symbols are vertical by default; rotate them 90 degrees.
items=[]
for p in parts:
    ispassive=p['kind'] in ('R','C','D','DZ','F');angle=90 if p['kind'] in ('R','C','F') else 0
    x,y=p['x'],p['y'];meta=pin_meta(p)
    # Diode native pins are1K left and2A right. R/C/F rotated90 gives1 left,2 right.
    h=max(5.08,max(abs(t[1]) for t in meta.values())+1.27)
    props=[prop('Reference',p['ref'],x,y-3 if ispassive else y-h-2.54,angle=angle),prop('Value',p['value'],x,y+3 if ispassive else y+h+2.54,angle=angle)]
    for name,val in [('Footprint',p['footprint']),('Datasheet',p['datasheet']),('LCSC',p['lcsc']),('LCSC Part #',p['lcsc']),('MPN',p['mpn']),('Manufacturer',p['manufacturer']),('Source URL',p['source_url']),('Role',p['role']),('Design Notes',p['note'])]: props.append(prop(name,val,x,y,True))
    items.append(f'(symbol (lib_id {q(symid(p))}) (at {x} {y} {angle}) (unit 1) (in_bom yes) (on_board yes) (uuid {p["uuid"]})'+''.join(props)+''.join(f'(pin {q(k)} (uuid {uid()}))' for k in p['pins'])+f'(instances (project "BSPD_2027" (path "/{sheet_id}" (reference {q(p["ref"])}) (unit 1)))))')
    for k,t in meta.items():
        px=x+t[0];py=y+t[1]
        net=p['pins'][k]
        if net is None:
            items.append(f'(no_connect (at {px} {py}) (uuid {uid()}))');continue
        dx=-10.16 if t[0]<0 else 10.16; ex=px+dx
        items.append(f'(wire (pts (xy {px} {py}) (xy {ex} {py})) (stroke (width 0) (type default)) (uuid {uid()}))')
        # local net labels attach at wire ends, away from symbol interiors.
        items.append(f'(global_label {q(net)} (shape input) (at {ex} {py} '+('180' if dx<0 else '0')+') (effects (font (size 1 1)) (justify left)) (uuid '+uid()+'))')

for n,(net,x,y) in enumerate([('VP',190.5,190.5),('GND',190.5,198.12)],1):
    items.append(f'(symbol (lib_id "Review:PWR_FLAG") (at {x} {y} 0) (unit 1) (in_bom no) (on_board no) (uuid {uid()})'+prop('Reference',f'#FLG{n}',x,y,True)+prop('Value','PWR_FLAG',x,y,True)+f'(instances (project "BSPD_2027" (path "/{sheet_id}" (reference "#FLG{n}") (unit 1)))))')
    items.append(f'(global_label {q(net)} (shape input) (at {x} {y} 0) (effects (font (size 1 1)) (justify left)) (uuid {uid()}))')

texts=[(20,20,'BSPD 2027 — ENGINEERING REVIEW / CALIBRATION REQUIRED'),
       (20,28,'Same Molex connector and pinout. Hardware only. External normally-open high-side shutdown relay required.'),
       (20,36,'All trimmers removed: thresholds are selected by soldered precision resistors. Do not order for vehicle use before release checks.'),
       (30,48,'1. CONNECTOR'),(105,43,'2. PROTECTED SUPPLY / REFERENCE'),(230,43,'3. CURRENT / SENSOR FAULTS / UV'),(410,43,'4. BRAKE / SENSOR FAULTS'),
       (30,225,'5. COINCIDENCE + NON-LATCHING PERMIT'),(230,252,'6. CONTINUOUS TIMING'),(410,245,'7. ACTIVE-HIGH OUTPUT'),
       (20,378,'FAULT_OK is wired-AND: sensor faults and undervoltage directly remove permit; only brake+current coincidence is delayed.'),
       (20,386,'PERMIT = FAULT_OK AND POR_N. The signal recovers when faults clear. Fault retention and manual reset belong to the external relayboard.'),
       (20,394,'DHAB S/134 channel 2: ideal 5kW @360V =13.8889A; nominal Vout=2.63889V @5.000V. Confirm direction and supply accuracy.'),
       (20,402,'AiM X05SNP13520: 0–135 bar / 1–5 V. Hard-brake pressure remains unconfirmed. Resistor population requires vehicle calibration.')]
for x,y,s in texts:items.append(f'(text {q(s)} (at {x} {y} 0) (effects (font (size 1.27 1.27)) (justify left bottom)) (uuid {uid()}))')

sch=f'(kicad_sch (version 20230121) (generator eeschema) (uuid {sheet_id}) (paper "A2") (title_block (title "BSPD 2027 engineering review") (rev "R2 — external relay latch") (date "2026-10-30")) (lib_symbols '+''.join(emit(s) for s in libsyms.values())+')'+''.join(items)+')'
(OUT/'BSPD_2027.kicad_sch').write_text(sch)
(OUT/'Review.kicad_sym').write_text('(kicad_symbol_lib (version 20220914) (generator kicad_symbol_editor) '+''.join(emit([s[0],Q(str(s[1]).split(':',1)[1])]+s[2:]) for s in libsyms.values())+')')
(OUT/'sym-lib-table').write_text('(sym_lib_table (version 7) (lib (name "Review") (type "KiCad") (uri "${KIPRJMOD}/Review.kicad_sym") (options "") (descr "BSPD physical-pin review symbols")))')
(ROOT/'circuit_spec.json').write_text(json.dumps(dict(sheet_uuid=sheet_id,parts=parts,release_status='ENGINEERING_REVIEW_CALIBRATION_PENDING'),indent=2))
groups={}
for p in parts:
    key=(p['lcsc'],p['value'],p['footprint'])
    groups.setdefault(key,[]).append(p['ref'])
with (OUT/'BSPD_2027_JLCPCB_BOM_REVIEW.csv').open('w',newline='') as f:
    w=csv.writer(f);w.writerow(['Comment','Designator','Footprint','LCSC Part #'])
    for (lcsc,value,fp),refs in groups.items():w.writerow([value,','.join(refs),fp.split(':')[-1],lcsc])
with (OUT/'BSPD_2027_detailed_BOM.csv').open('w',newline='') as f:
    w=csv.writer(f);w.writerow(['Reference','Value','Manufacturer','MPN','LCSC','Footprint','Role','Source URL','Design Notes'])
    for p in parts:w.writerow([p[k] for k in ['ref','value','manufacturer','mpn','lcsc','footprint','role','source_url','note']])
print(f'Generated {len(parts)} physical components')
