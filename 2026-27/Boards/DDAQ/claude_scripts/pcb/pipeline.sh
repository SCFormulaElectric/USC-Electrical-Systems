#!/bin/sh
# Full layout pipeline up to the autorouter input.  Usage: pipeline.sh <scratch_dir> <kicad_project_copy_dir>
# needs: stage0 board from build_board.py at $1/stage0.kicad_pcb and groups at $1/groups.json
set -e
S=$1; P=$2; D=$(cd "$(dirname "$0")" && pwd)
RUN="docker run --rm -u 0 -v /home/user:/home/user -v $S:$S -v $P:$P -w $P --entrypoint python3 kicad/kicad:10.0.8-amd64"
$RUN $D/place.py $S/stage0.kicad_pcb $S/groups.json $P/DDAQ.kicad_pcb /usr/share/kicad/footprints
$RUN $D/zones.py $P/DDAQ.kicad_pcb
$RUN $D/fanout.py $P/DDAQ.kicad_pcb
$RUN $D/powerpour.py $P/DDAQ.kicad_pcb
$RUN -c "import sys,pcbnew; b=pcbnew.LoadBoard('$P/DDAQ.kicad_pcb'); print('dsn', pcbnew.ExportSpecctraDSN(b,'$P/DDAQ.dsn'))"
