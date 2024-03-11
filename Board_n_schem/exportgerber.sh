#!/bin/bash

if [ $# -lt 1 ]; then
    echo "Bro try again: $0 directory1, directory2 ... "
    exit 1
fi

mkdir -p ./temp_gerbers

for directory in "$@"; do
    if [ ! -d "$directory" ]; then
        echo "Directory '$directory' not found."
        continue
    fi

    temp_dir=$(mktemp -d)
    trap 'rm -rf "$temp_dir"' EXIT

    for file in "$directory"/*.kicad_pcb; do
        if [ -f "$file" ]; then

		#optimized for JLCPCB:
		kicad-cli pcb export gerbers \
		    --output "$temp_dir" \
		    --layers F.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts,In1.Cu,In2.Cu \
		    --exclude-value \
		    --include-border-title \
		    --no-x2 \
		    --no-netlist \
		    --subtract-soldermask \
		    "$file" &>/dev/null
	    echo "Exported gerbers for: $file"
		kicad-cli pcb export drill \
    		    -o "$temp_dir/" \
    		    --format excellon \
    		    --drill-origin absolute \
    		    --excellon-zeros-format decimal \
    		    --excellon-units mm \
    		    --excellon-oval-format alternate \
    		    --generate-map \
    		    --map-format gerberx2 \
		    "$file" &>/dev/null
            echo "Exported drill file for: $file"
        fi
    done
# optimized for staelens' aribtrary format
    zip_file="./temp_gerbers/$(date +"%m%d%Y")_${directory##*/}_"$name".zip"
    zip -r "$zip_file" "$temp_dir" &>/dev/null

    rm -rf "$temp_dir"

    echo "Exported files zipped to: $zip_file"
done

exit 0

