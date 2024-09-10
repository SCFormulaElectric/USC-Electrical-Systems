#!/bin/bash

# Author: Arda Caliskan
# Changelist:
# 7/3/24 - v1.1 Updated to support up to 6 layers
# 9/9/24 - v1.2 Updated to prompt user for the number of layers in their board
# REQUIREMENTS:
# Unix based OS, kicad-cli, zip


if [ $# -lt 1 ]; then
    echo "Bro try again: $0 directory1, directory2 ... "
    exit 1
fi

# Prompt user for their name and store it in $name
read -p "Enter your name: " name

# Prompt user for the number of layers
read -p "Enter the number of layers on your board: " layers

# Define the layers to export based on the number of layers
case "$layers" in
    2)
        layer_list="F.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts"
        ;;
    3)
        layer_list="F.Cu,In1.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts"
        ;;
    4)
        layer_list="F.Cu,In1.Cu,In2.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts"
        ;;
	5)
        layer_list="F.Cu,In1.Cu,In2.Cu,In3.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts"
        ;;
    6)
        layer_list="F.Cu,In1.Cu,In2.Cu,In3.Cu,In4.Cu,B.Cu,F.Paste,B.Paste,F.SilkS,B.SilkS,F.Mask,B.Mask,Edge.Cuts"
        ;;
    *)
        echo "Invalid number of layers. Only 2, 3, 4, and 6 are supported."
        exit 1
        ;;
esac

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
            # Export Gerbers based on layer count
            kicad-cli pcb export gerbers \
                --output "$temp_dir" \
                --layers "$layer_list" \
                --exclude-value \
                --include-border-title \
                --no-x2 \
                --no-netlist \
                --subtract-soldermask \
                "$file" &>/dev/null
            echo "Exported gerbers for: $file"

            # Export drill file
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

    # Zip the output files
    zip_file="./temp_gerbers/$(date +"%m%d%Y")_${directory##*/}_${name}.zip"
    zip -r "$zip_file" "$temp_dir" &>/dev/null

    rm -rf "$temp_dir"

    echo "Exported files zipped to: $zip_file"
done

exit 0
