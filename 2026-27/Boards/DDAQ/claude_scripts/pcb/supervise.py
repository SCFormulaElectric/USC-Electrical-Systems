"""Unattended Freerouting supervisor: restart stalled runs, keep the best result, continue from it.

python3 supervise.py <workdir> <prerouted.kicad_pcb> <fresh.dsn> <freerouting.jar> <minutes>
Writes progress lines to <workdir>/progress.log and the best routed board to <workdir>/best.kicad_pcb
(best = fewest unconnected items reported by KiCad DRC after importing the session).
Needs: java, docker image kicad/kicad:10.0.8-amd64, kicad-cli wrapper in $KICAD_CLI.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import time

work, base, fresh_dsn, jar, minutes = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], float(sys.argv[5])
deadline = time.time() + minutes * 60
KCLI = os.environ['KICAD_CLI']
proj_dir = os.path.dirname(base)
os.makedirs(work, exist_ok=True)
LOG = os.path.join(work, 'progress.log')
DOCKER = ['docker', 'run', '--rm', '-u', '0', '-v', '/home/user:/home/user', '-v', f'{work}:{work}', '-v',
          f'{proj_dir}:{proj_dir}', '-w', proj_dir, '--entrypoint', 'python3', 'kicad/kicad:10.0.8-amd64']


def log(msg):
    line = time.strftime('%H:%M:%S ') + msg
    with open(LOG, 'a') as f:
        f.write(line + '\n')
    print(line, flush=True)


def py(code):
    return subprocess.run(DOCKER + ['-c', code], capture_output=True, text=True, timeout=900)


def import_and_count(ses, out_board):
    """Import ses into the pre-routed board, refill zones, return KiCad DRC unconnected count."""
    r = py(f"import pcbnew; b=pcbnew.LoadBoard({base!r}); ok=pcbnew.ImportSpecctraSES(b,{ses!r}); "
           f"pcbnew.ZONE_FILLER(b).Fill(b.Zones()); b.Save({out_board!r}); print('ok', ok)")
    if 'ok True' not in r.stdout:
        log(f'import failed: {r.stdout[-200:]} {r.stderr[-200:]}')
        return None
    # DRC needs the project files next to the board
    chk = os.path.join(proj_dir, '_chk.kicad_pcb')
    shutil.copy(out_board, os.path.join(proj_dir, 'DDAQ_chk.kicad_pcb'))
    for ext in ('kicad_pro', 'kicad_dru'):
        src = os.path.join(proj_dir, f'DDAQ.{ext}')
        if os.path.exists(src):
            shutil.copy(src, os.path.join(proj_dir, f'DDAQ_chk.{ext}'))
    rep = os.path.join(work, 'drc.json')
    subprocess.run([KCLI, 'pcb', 'drc', '--format', 'json', '--severity-all', '--units', 'mm', '-o', rep,
                    os.path.join(proj_dir, 'DDAQ_chk.kicad_pcb')], capture_output=True, timeout=900, cwd=proj_dir)
    d = json.load(open(rep))
    clr = sum(1 for v in d['violations'] if v['type'] in ('clearance', 'shorting_items', 'hole_to_hole'))
    return len(d['unconnected_items']), clr


def run(dsn, timeout_min, stall_check):
    """One Freerouting job. Returns (ses_path or None, passes list, reason)."""
    rd = os.path.join(work, f'run_{int(time.time())}')
    os.makedirs(rd)
    shutil.copy(dsn, os.path.join(rd, 'in.dsn'))
    out = os.path.join(rd, 'out.ses')
    flog = open(os.path.join(rd, 'fr.log'), 'w')
    p = subprocess.Popen(['java', '-jar', jar, '-de', os.path.join(rd, 'in.dsn'), '-do', out, '--gui.enabled=false',
                          '--router.max_passes=200', f'--router.job_timeout=00:{timeout_min:02d}:00',
                          '--router.optimizer.enabled=false', '--usage_and_diagnostic_data.disable_analytics=true'],
                         cwd=rd, stdout=flog, stderr=subprocess.STDOUT)
    passes, reason = [], 'finished'
    while p.poll() is None:
        time.sleep(15)
        txt = open(os.path.join(rd, 'fr.log'), errors='ignore').read()
        new = [int(m) for m in re.findall(r'Auto-router pass #\d+ .*?\((\d+) unrouted\)', txt)]
        for k in new[len(passes):]:
            log(f'  pass {len(passes) + 1}: {k} unrouted')
            passes.append(k)
        if stall_check and len(passes) >= 3 and passes[2] > 0.93 * passes[0]:
            p.kill(); p.wait(); reason = 'stalled'
            break
        if time.time() > deadline + 120:
            p.kill(); p.wait(); reason = 'deadline'
            break
    return (out if os.path.exists(out) else None), passes, reason


best = None  # (unconnected, board path)
mode = 'fresh'
fails_in_cont = 0
log(f'supervisor start, budget {minutes:.0f} min')
while time.time() < deadline - 12 * 60:
    if mode == 'fresh':
        log('fresh run (20 min max, restart if stalled by pass 3)')
        ses, passes, why = run(fresh_dsn, 20, True)
    else:
        cdsn = os.path.join(work, 'cont.dsn')
        r = py(f"import pcbnew; b=pcbnew.LoadBoard({best[1]!r}); print(pcbnew.ExportSpecctraDSN(b,{cdsn!r}))")
        log('continuation run from best (15 min)')
        ses, passes, why = run(cdsn, 15, False)
    log(f'  run ended: {why}, passes={len(passes)}')
    if not ses:
        mode = 'fresh'
        continue
    cand = os.path.join(work, f'cand_{int(time.time())}.kicad_pcb')
    res = import_and_count(ses, cand)
    if res is None:
        mode = 'fresh'; continue
    unc, clr = res
    log(f'  imported: {unc} unconnected in KiCad, {clr} clearance/hole errors')
    if clr == 0 and (best is None or unc < best[0]):
        best = (unc, cand)
        shutil.copy(cand, os.path.join(work, 'best.kicad_pcb'))
        log(f'  NEW BEST: {unc} unconnected')
        mode, fails_in_cont = 'cont', 0
        if unc == 0:
            break
    else:
        fails_in_cont += 1
        mode = 'cont' if (best and fails_in_cont < 2) else 'fresh'
log(f'supervisor done; best = {best[0] if best else None} unconnected')
