"""Refresh review manufacturing outputs using the checked native PCB."""
from pathlib import Path
import subprocess,shutil,csv,json,zipfile
R=Path(__file__).resolve().parents[1]
CLI='/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli'
pcb='revised/BSPD_2027.kicad_pcb'
fab=R/'revised/fabrication_REVIEW'
if fab.exists():
    shutil.copytree(fab,R/'before/fabrication_REVIEW',dirs_exist_ok=True)
    shutil.rmtree(fab)
fab.mkdir()
jobs=[
 ['pcb','export','gerbers','--layers','F.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts','--use-drill-file-origin','--output','revised/fabrication_REVIEW/',pcb],
 ['pcb','export','drill','--format','excellon','--drill-origin','plot','--excellon-units','mm','--excellon-separate-th','--generate-report','--report-path','reports/drill_report.txt','--output','revised/fabrication_REVIEW/',pcb],
 ['pcb','export','pos','--format','csv','--units','mm','--use-drill-file-origin','--output','revised/BSPD_2027_all_KiCad_positions.csv',pcb],
 ['pcb','export','pos','--format','csv','--units','mm','--use-drill-file-origin','--smd-only','--exclude-fp-th','--output','revised/BSPD_2027_SMT_KiCad_positions.csv',pcb],
]
logs=[]
for args in jobs:
    result=subprocess.run([CLI]+args,cwd=R,capture_output=True,text=True)
    logs.append({'command':args,'returncode':result.returncode,'stdout':result.stdout,'stderr':result.stderr})
    if result.returncode:
        print(result.stdout,result.stderr)
        raise SystemExit(result.returncode)
    print('Exported '+' '.join(args[:3]),flush=True)
(R/'reports/manufacturing_exports.json').write_text(json.dumps(logs,indent=2)+'\n')
with (R/'revised/BSPD_2027_SMT_KiCad_positions.csv').open(newline='') as f:
    rows=list(csv.DictReader(f))
assert len(rows)==65,len(rows)
with (R/'revised/BSPD_2027_JLCPCB_CPL_SMT_REVIEW.csv').open('w',newline='') as f:
    w=csv.writer(f);w.writerow(['Designator','Mid X','Mid Y','Layer','Rotation'])
    for row in rows:
        w.writerow([row['Ref'],row['PosX'],row['PosY'],'Top' if row['Side'].lower() in ['top','front'] else 'Bottom',row['Rot']])
(fab/'README_REVIEW.txt').write_text('R3 brake-sensor calibration review, November 4 2026. Not released for vehicle manufacture. Gerber/drill/placement origin is the board drill/place origin. Four 4mm mounting holes are routed Edge.Cuts circles. See DESIGN_REVIEW.md.\n')
with zipfile.ZipFile(R/'revised/BSPD_2027_Gerbers_REVIEW_NOT_RELEASED.zip','w',zipfile.ZIP_DEFLATED) as z:
    for p in sorted(fab.iterdir()):
        if p.is_file():z.write(p,p.name)
print('Updated 65-part CPL and Gerber archive',flush=True)
