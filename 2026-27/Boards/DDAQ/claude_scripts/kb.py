# /// script
# requires-python = ">=3.11"
# dependencies = ["mcp-server-kicad==0.21.1", "pymupdf>=1.24"]
# ///
import os, sys, json, importlib.util
P="C:/Git/USC-Electrical-Systems/2026-27/Boards/DDAQ/DDAQ"
os.environ.update(KICAD_SCH_PATH=P+"/DDAQ.kicad_sch", KICAD_PCB_PATH=P+"/DDAQ.kicad_pcb", KICAD_OUTPUT_DIR=P,
                  KICAD_BIN="C:/Program Files/KiCad/10.0/bin", KICAD_CLI_PATH="C:/Program Files/KiCad/10.0/bin/kicad-cli.exe")
sys.stdout.reconfigure(encoding="utf-8")
spec=importlib.util.spec_from_file_location("kbserver","C:/Git/USC-Electrical-Systems/tools/kicad-batch/server.py")
kb=importlib.util.module_from_spec(spec); spec.loader.exec_module(kb)
if __name__=="__main__":
    mode=sys.argv[1]
    if mode=="tools":
        t=kb._tools(); print(sorted(t))
    elif mode=="batch":
        calls=json.load(open(sys.argv[2],encoding="utf-8"))
        print(kb.batch(calls, result_chars=int(sys.argv[3]) if len(sys.argv)>3 else 0))
