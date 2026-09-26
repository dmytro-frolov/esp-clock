#!/usr/bin/env bash

set -e

python_bin="${PYTHON:-python}"
modules=(modes.py display.py time_handler.py)

version="$("$python_bin" -m mpy_cross --version)"
case "$version" in
    *"v1.20.0"*"mpy v6"*) ;;
    *)
        echo "Expected mpy-cross 1.20.0 with mpy v6, got: $version" >&2
        exit 1
        ;;
esac

mkdir -p build

if [ "$#" -gt 0 ]; then
    modules=("$@")
fi

for source in "${modules[@]}"; do
    output="build/${source%.py}.mpy"
    "$python_bin" -m mpy_cross -msmall-int-bits=31 -o "$output" "$source"
    echo "$source -> $output"
done
