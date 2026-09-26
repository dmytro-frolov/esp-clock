# Esp clock

## Hardware
* esp8266 nodemcu
* 4 segment led display based on 74HC595
* active buzzer
* EC11 encoder: `CLK` → D1/GPIO5, `DT` → D2/GPIO4,
  `SW` → D6/GPIO12, second `SW` contact → GND
* DS3231 RTC

## Operating modes

Turn the rotary encoder to switch cyclically between three modes:

1. **Clock** — current time in `HH:MM` format with a blinking dot.
2. **Stopwatch** — shared elapsed time in `MM:SS` format.
3. **Hour stopwatch** — the same elapsed time in `HH:MM` format.

Press the encoder in either stopwatch mode to pause or resume. The second dot
blinks while running and stays on while paused. Switching between stopwatch
modes preserves the counter; switching to the clock pauses it. The maximum is
`99:59:59`, displayed as `59:59` in mode 2 and `99:59` in mode 3.

## Firmware installation
This project depends on MicroPython `ESP8266_GENERIC-20230426-v1.20.0.bin`.

Use the firmware file stored in the repository root:
- [`ESP8266_GENERIC-20230426-v1.20.0.bin`](~/git/esp-clock/ESP8266_GENERIC-20230426-v1.20.0.bin)

This version is effectively required because the project uses precompiled `.mpy` modules in [`libs/`](~/git/esp-clock/libs), and those can break on other MicroPython versions.

Full erase is not required on every update. Use `erase_flash` only when you want a completely clean device or when you suspect filesystem/firmware incompatibility.

Clean flash example:
```bash
python -m esptool --chip esp8266 -p /dev/cu.usbserial-21220 --baud 460800 erase-flash
python -m esptool --chip esp8266 -p /dev/cu.usbserial-21220 --baud 460800 \
  write-flash --flash-size detect 0 ESP8266_GENERIC-20230426-v1.20.0.bin
```

Firmware update without full erase:
```bash
python -m esptool --chip esp8266 -p /dev/cu.usbserial-21220 --baud 460800 \
  write-flash --flash-size detect 0 ESP8266_GENERIC-20230426-v1.20.0.bin
```

## Configuration

Create a local Wi-Fi configuration file if NTP sync is required:

```bash
cp .env.example .env
```

Then edit `.env`:

```python
WIFI_SSID = "your-wifi-name"
WIFI_PASSWORD = "your-wifi-password"
```

The file is ignored by Git and uploaded to the device as `secrets.py`. If it is
missing or the credentials are wrong, the clock still boots, but NTP will not
update the RTC.

## Build

Create a virtual environment and install the development tools. The
`mpy-cross` version is pinned to the firmware version:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
```

Run the host-side tests and compile the memory-heavy application modules:

```bash
python -m unittest discover -s tests -v
./build.sh
```

The tests provide local stubs for the ESP8266 hardware modules; no board or
third-party test dependencies are required. The build produces
`build/modes.mpy`, `build/display.mpy`, and `build/time_handler.mpy` using
`mpy-cross` 1.20.0. Precompiled modules avoid the temporary RAM cost of parsing
their source on the ESP8266.

Do not leave same-named `.py` files on the device: MicroPython loads `.py`
before `.mpy`. `flash.sh` removes those source files automatically.

## Flash
`ampy` configuration can be found at [`.ampy`](~/git/esp-clock/.ampy).

Use [`flash.sh`](~/git/esp-clock/flash.sh) to upload the project files:
```bash
./flash.sh
```

The script:
- runs `build.sh`
- uploads all required files
- uploads the heavy application modules as `.mpy`
- uploads `.env` as `secrets.py` when present
- creates `libs` directories if needed
- waits `1` second after each `ampy` command
- performs a real cold boot over USB-UART
- fails on `Traceback`, `MemoryError`, or less than 5 KB of free heap

To upload only files that changed, pass them as arguments. This does not erase
the device filesystem or reinstall MicroPython:

```bash
./flash.sh modes.py
```

Passing `modes.py`, `display.py`, or `time_handler.py` uploads the corresponding
compiled `.mpy` file and removes the old `.py` file from the device.

After creating or changing the Wi-Fi configuration, upload both files:

```bash
./flash.sh modes.py .env
```

Manual examples:
```bash
ampy ls
ampy put main.py
ampy reset
```

The application prints `Free heap before main: N` during boot. For detailed
manual diagnostics, run `gc.collect()`, `gc.mem_free()`, and
`micropython.mem_info(1)` in the REPL.

## Recovery
If the clock does not work after reflashing, check these in order:

1. Verify that the firmware is exactly [`ESP8266_GENERIC-20230426-v1.20.0.bin`](~/git/esp-clock/ESP8266_GENERIC-20230426-v1.20.0.bin).
2. Verify that `modes.mpy`, `display.mpy`, and `time_handler.mpy` are present and
   their same-named `.py` files are absent.
3. Verify Wi-Fi credentials in `.env` if NTP sync is expected to update the RTC.
4. Run `python tools/smoke_test.py` to capture a cold-boot log and memory check.

Typical symptoms:
- Empty display after boot: usually wrong firmware version, missing files, or an import-time crash.
- `MemoryError` during import: rebuild and upload `.mpy` files with `./flash.sh`.
- Time is off by one hour: usually RTC was not updated because Wi-Fi or NTP sync did not complete.
- Reflash needed: full `erase_flash` is only necessary when you want a clean device or suspect a broken flash state.
