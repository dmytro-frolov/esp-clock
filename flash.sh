#!/usr/bin/env bash

set -e

python_bin="${PYTHON:-python}"

./build.sh

upload_file() {
    case "$1" in
        .env)
            ampy put .env secrets.py
            ;;
        modes.py|display.py|time_handler.py)
            remote_mpy="${1%.py}.mpy"
            ampy rm "$1" 2>/dev/null || true
            ampy put "build/$remote_mpy" "$remote_mpy"
            ;;
        *)
            ampy put "$1"
            ;;
    esac
    sleep 1
}

finish() {
    "$python_bin" tools/smoke_test.py
}

if [ "$#" -gt 0 ]; then
    for file in "$@"; do
        upload_file "$file"
    done
    finish
    exit
fi

mkdir_if_missing() {
    ampy mkdir "$1" 2>/dev/null || true
    sleep 1
}

ampy ls
sleep 1

upload_file boot.py
upload_file main.py
upload_file modes.py
upload_file display.py
upload_file time_handler.py
upload_file beeper.py

if [ -f .env ]; then
    upload_file .env
fi

mkdir_if_missing libs

ampy put libs/__init__.py libs/__init__.py
sleep 1

ampy put libs/_ds3231.py libs/_ds3231.py
sleep 1

ampy put libs/ds3231.mpy libs/ds3231.mpy
sleep 1

ampy put libs/_rotary.py libs/_rotary.py
sleep 1

ampy put libs/_rotary_irq.py libs/_rotary_irq.py
sleep 1

ampy put libs/rotary.mpy libs/rotary.mpy
sleep 1

ampy put libs/rotary_irq.mpy libs/rotary_irq.mpy
sleep 1

mkdir_if_missing libs/datetime

ampy put libs/datetime/__init__.py libs/datetime/__init__.py
sleep 1

ampy put libs/datetime/_date.py libs/datetime/_date.py
sleep 1

ampy put libs/datetime/_datetime.py libs/datetime/_datetime.py
sleep 1

ampy put libs/datetime/_dt.py libs/datetime/_dt.py
sleep 1

ampy put libs/datetime/_time.py libs/datetime/_time.py
sleep 1

ampy put libs/datetime/_timedelta.py libs/datetime/_timedelta.py
sleep 1

ampy put libs/datetime/_timezone.py libs/datetime/_timezone.py
sleep 1

ampy put libs/datetime/date.mpy libs/datetime/date.mpy
sleep 1

ampy put libs/datetime/datetime.mpy libs/datetime/datetime.mpy
sleep 1

ampy put libs/datetime/dt.mpy libs/datetime/dt.mpy
sleep 1

ampy put libs/datetime/time.mpy libs/datetime/time.mpy
sleep 1

ampy put libs/datetime/timedelta.mpy libs/datetime/timedelta.mpy
sleep 1

ampy put libs/datetime/timezone.mpy libs/datetime/timezone.mpy
sleep 1

finish
