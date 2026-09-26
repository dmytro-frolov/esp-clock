# AGENTS.md

## Purpose
`esp-clock` is a MicroPython firmware project for an ESP8266-based desk clock. The device uses:

- ESP8266 NodeMCU
- 4-digit 7-segment LED display driven through `74HC595`
- DS3231 RTC over I2C
- EC11 rotary encoder for mode selection
- Active buzzer

The codebase is small and hardware-oriented. Most changes should preserve boot reliability, low memory use, and simple event-loop behavior.

## Runtime Architecture
- [`main.py`](/Users/nvxd8c/git/esp-clock/main.py): entrypoint. Runs initial time sync via `mode.get_time()`, then starts the display refresh loop and mode listener concurrently with `uasyncio`.
- [`modes.py`](/Users/nvxd8c/git/esp-clock/modes.py): UI state machine. Owns the rotary encoder, mode switching, startup animation, Wi-Fi connection helper, and the concrete display modes (`Clock`, `StopWatch`, `HourStopWatch`).
- [`display.py`](/Users/nvxd8c/git/esp-clock/display.py): low-level 4-digit multiplexed display driver over SPI plus latch pin control.
- [`time_handler.py`](/Users/nvxd8c/git/esp-clock/time_handler.py): time source abstraction. Syncs from NTP when Wi-Fi is available, calculates Kyiv DST offset manually, stores the result in DS3231, and reads current time back from the RTC.
- [`beeper.py`](/Users/nvxd8c/git/esp-clock/beeper.py): simple async pulse for the active buzzer.
- [`boot.py`](/Users/nvxd8c/git/esp-clock/boot.py): currently empty aside from the standard comment.
- `libs/`: vendored MicroPython support modules and precompiled `.mpy` files. Treat these as runtime dependencies, not normal app code.

## Hardware Assumptions
Current pin usage inferred from the code:

- Rotary encoder CLK: GPIO5
- Rotary encoder DT: GPIO4
- Rotary encoder SW: GPIO12 (D6), active low to GND
- Display latch (`rclk`): GPIO16
- I2C SDA for DS3231: GPIO0
- I2C SCL for DS3231: GPIO2
- Buzzer: GPIO15
- Display data path uses `SPI(1)`

Do not change pin assignments casually. They are effectively part of the device contract.

## Development Rules
- Keep code compatible with MicroPython on ESP8266. Avoid CPython-only features and heavyweight dependencies.
- Prefer small allocations and simple control flow. The project already uses `.mpy` bytecode in `libs/` to reduce memory pressure.
- The expected firmware is [`ESP8266_GENERIC-20230426-v1.20.0.bin`](/Users/nvxd8c/git/esp-clock/ESP8266_GENERIC-20230426-v1.20.0.bin). Treat MicroPython `v1.20.0` on `ESP8266_GENERIC` as required unless the `.mpy` files are rebuilt for another version.
- Preserve the asynchronous display refresh loop in [`display.py`](/Users/nvxd8c/git/esp-clock/display.py). Blocking work here will cause visible flicker.
- Be careful with long blocking sleeps in mode logic. The UI depends on `uasyncio` scheduling staying responsive.
- NTP sync depends on Wi-Fi credentials from the local `.env`, uploaded as `secrets.py`. If time sync appears broken after a flash, verify that file first.
- Timezone logic in [`time_handler.py`](/Users/nvxd8c/git/esp-clock/time_handler.py) is custom and Kyiv-specific. If changing it, verify DST boundary behavior explicitly.
- `Display.clear()` only clears decimal dots; it does not blank digits. If a task depends on a full display reset, inspect call sites carefully.
- `Modes.exit()` cancels tasks and clears the task list. When changing mode lifecycle behavior, preserve both parts.

## Build And Flash Workflow
- Flash MicroPython firmware from [`ESP8266_GENERIC-20230426-v1.20.0.bin`](/Users/nvxd8c/git/esp-clock/ESP8266_GENERIC-20230426-v1.20.0.bin).
- Full `erase_flash` is not required for every update. Use it when you need a clean device or when debugging a bad flash state.
- Run `build.sh` with `mpy-cross` 1.20.0 to compile `modes.py`, `display.py`, and `time_handler.py` before upload.
- Use [`flash.sh`](/Users/nvxd8c/git/esp-clock/flash.sh) for routine file uploads. Device connection defaults live in [`.ampy`](/Users/nvxd8c/git/esp-clock/.ampy).
- `flash.sh` uploads compiled application modules, removes their same-named `.py` files, and runs a cold-boot smoke test with a 5 KB minimum free-heap check.

Typical commands from the repo documentation:

```bash
./flash.sh
python -m unittest discover -s tests -v
ampy ls
ampy reset
```

## Validation Expectations
- Run the host-side `unittest` suite for application logic.
- Run the cold-boot smoke test on hardware after flashing; host tests cannot reproduce ESP8266 heap pressure.
- For code changes, validate by static review first and, when hardware access is available, by running on the board.
- High-risk areas are:
  - display refresh timing
  - RTC read/write tuple formatting
  - NTP sync and timezone conversion
  - mode switching and task cancellation

## Repository Hygiene
- The worktree may contain local IDE files under `.idea/` and macOS metadata like `.DS_Store`. Do not rely on them.
- Avoid editing vendored `libs/` modules unless the task explicitly requires it.
- Prefer focused changes in the application modules over broad refactors. This project is small enough that clarity matters more than abstraction.
