
# Esp clock

## Hardware
* esp8266 nodemcu
* 4 segment led display based on 74HC595
* active buzzer
* EC11 encoder
* DS3231 RTC

## Firmware installation
Based on [micropython](https://micropython.org/download/): \
```esptool.py --chip esp8266 -p /dev/cu.usbserial-14820 --baud 460800 erase_flash && esptool.py --chip esp8266 -p /dev/cu.usbserial-14820 --baud 460800 write_flash --flash_size=detect 0 esp8266-20230426-v1.20.0.bin```

## Bytecode compilation
In order to improve memory consumption use `mpy_cross` example: ```python -m mpy_cross _datetime.py -o datetime.mpy```

## Flash
In this project I used MicroPython pycharm plugin, I think it's based on this [tool](https://github.com/JetBrains/intellij-micropython/blob/master/scripts/microupload.py). Just upload everyfile in the folder to your board.
