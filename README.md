# Esp clock

## Hardware
* esp8266 nodemcu
* 4 segment led display based on 74HC595
* active buzzer
* EC11 encoder
* DS3231 RTC

## Operating modes

Turn the rotary encoder to switch cyclically between four modes:

1. **Clock** — current time in `HH:MM` format with a blinking dot.
2. **Date** — current date in `DD.MM` format.
3. **Stopwatch** — elapsed time in `MM:SS` format.
4. **Hour stopwatch** — elapsed time in `HH:MM` format.

## Firmware installation
This project depends on MicroPython `ESP8266_GENERIC-20230426-v1.20.0.bin`.

Use the firmware file stored in the repository root:
- [`ESP8266_GENERIC-20230426-v1.20.0.bin`](~/git/esp-clock/ESP8266_GENERIC-20230426-v1.20.0.bin)

This version is effectively required because the project uses precompiled `.mpy` modules in [`libs/`](~/git/esp-clock/libs), and those can break on other MicroPython versions.

Full erase is not required on every update. Use `erase_flash` only when you want a completely clean device or when you suspect filesystem/firmware incompatibility.

Clean flash example:
```bash
esptool.py --chip esp8266 -p /dev/cu.usbserial-14320 --baud 460800 erase_flash
esptool.py --chip esp8266 -p /dev/cu.usbserial-14320 --baud 460800 write_flash --flash_size=detect 0 ESP8266_GENERIC-20230426-v1.20.0.bin
```

Firmware update without full erase:
```bash
esptool.py --chip esp8266 -p /dev/cu.usbserial-14320 --baud 460800 write_flash --flash_size=detect 0 ESP8266_GENERIC-20230426-v1.20.0.bin
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

Application files do not require compilation. Run the host-side checks before
uploading:

```bash
python -m unittest discover -s tests -v
```

The tests provide local stubs for the ESP8266 hardware modules; no board or
third-party test dependencies are required.

The vendored `.mpy` libraries are already compiled for the required firmware.
Recompile them with `mpy_cross` only after changing a library source file.

## Bytecode compilation
In order to improve memory consumption use `mpy_cross` example: ```python -m mpy_cross _datetime.py -o datetime.mpy```

## Flash
`ampy` configuration can be found at [`.ampy`](~/git/esp-clock/.ampy).

Use [`flash.sh`](~/git/esp-clock/flash.sh) to upload the project files:
```bash
./flash.sh
```

The script:
- uploads all required files
- uploads `.env` as `secrets.py` when present
- creates `libs` directories if needed
- waits `1` second after each `ampy` command
- finishes with `ampy reset`

To upload only files that changed, pass them as arguments. This does not erase
the device filesystem or reinstall MicroPython:

```bash
./flash.sh modes.py
```

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

## Recovery
If the clock does not work after reflashing, check these in order:

1. Verify that the firmware is exactly [`ESP8266_GENERIC-20230426-v1.20.0.bin`](~/git/esp-clock/ESP8266_GENERIC-20230426-v1.20.0.bin).
2. Verify that all runtime files are present on the device with `ampy ls`, `ampy ls /libs`, and `ampy ls /libs/datetime`.
3. Verify Wi-Fi credentials in `.env` if NTP sync is expected to update the RTC.
4. Run `ampy reset` after uploading files.

Typical symptoms:
- Empty display after boot: usually wrong firmware version, missing files, or an import-time crash.
- Time is off by one hour: usually RTC was not updated because Wi-Fi or NTP sync did not complete.
- Reflash needed: full `erase_flash` is only necessary when you want a clean device or suspect a broken flash state.
