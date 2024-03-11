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

            kicad-cli pcb export gerbers -o "$temp_dir" "$file" &>/dev/null

            echo "Exported gerbers for file: $file"
        fi
    done

    zip_file="./temp_gerbers/${directory##*/}_gerber_$(date +"%Y_%m_%d_%H_%M").zip"
    zip -r "$zip_file" "$temp_dir" &>/dev/null

    rm -rf "$temp_dir"

    echo "Exported files zipped to: $zip_file"
done

exit 0

