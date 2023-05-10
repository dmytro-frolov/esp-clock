import os

import mip
import time
import network
import ntptime
import uasyncio
import urequests

from machine import Pin, SPI, RTC, I2C

from libs.datetime import datetime
from libs.datetime import timezone
from libs.datetime import timedelta
from libs import DS3231


modules_to_install = []

# some embedded ports use epoch of 2000-01-01 00:00:00 UTC
if time.gmtime(0)[0] == 2000:
    EPOCH_FIX = 946684800 # check
else:
    EPOCH_FIX = 0

# EPOCH_FIX = 946677600

# try:
#     from datetime import datetime
# except ImportError:
#     modules_to_install.append(("datetime",
#                               "https://raw.githubusercontent.com/micropython/micropython-lib/master/python-stdlib/datetime/datetime.py"))
#


class Digit:
    digits: list

    dot = False
    number = 0

    def __init__(self, y):
        self.digits = [
            0b11000000,
            0b11111001,
            0b10100100,
            0b10110000,
            0b10011001,
            0b10010010,
            0b10000010,
            0b11111000,
            0b10000000,
            0b10010000,
        ]

        self.set(y)

    def set(self, y):
        self.number = y
        return self.digits[y]

    def get(self):
        if self.dot:
            return self.digits[self.number] - 0b10000000

        return self.digits[self.number]

    def toggle_dot(self):
        self.dot = not self.dot


class Display:
    places = [8, 4, 2, 1]

    def __init__(self) -> None:
        self.spi = SPI(1, 10000000)
        self.clr = Pin(16, Pin.OUT)
        self.rclk = Pin(5, Pin.OUT)

        self.digits = [Digit(0), Digit(0), Digit(0), Digit(0)]

        self.clr(0)

    def set(self, numbs: int | str):
        # this whole set and get is stupid, but it's mvp
        if isinstance(numbs, str):
            assert numbs.isdigit()

        if int(numbs) > 9999:
            self.set(0)

        numbs = "{:04}".format(int(numbs))
        for n, d in zip(numbs, self.digits):
            d.set(int(n))

    def get(self) -> str:
        return "".join([str(d.number) for d in self.digits])

    def latch(self):
        self.rclk(1)
        self.rclk(0)

    async def loop(self):
        self.clr(1)
        buf = bytearray(2)

        while True:
            for place, digit in zip(self.places, self.digits):
                buf[0] = digit.get()
                buf[1] = place

                self.spi.write(buf)
                self.latch()

                await uasyncio.sleep_ms(1)

    async def tick(self):
        while True:
            self.set(int(self.get()) + 1)

            self.digits[1].toggle_dot()
            await uasyncio.sleep(1)


def do_connect():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('connecting to network...')
        wlan.connect(os.environ["ssid"], os.environ["pass"])  # connect to an AP
        while not wlan.isconnected():
            pass
    print('network config:', wlan.ifconfig())

    return wlan.isconnected()


class TimeHandler:
    offset = 0

    def _get_from_worldtimeapi(self):
        try:
            resp = urequests.get("http://worldtimeapi.org/api/ip")
            if resp.status_code == 200:
                resp = resp.json()
                self.unixtime = resp["unixtime"]
                # todo: offset with minutes
                self.offset = int(resp["utc_offset"].split(':')[0])

        except Exception:
            return False

    def _get_from_std_lib(self):
        return ntptime.settime()

    def __init__(self):
        self._get_from_worldtimeapi()

        delta = timedelta(hours=self.offset)
        tz = timezone(delta)
        epoch = self.unixtime - EPOCH_FIX

        self.datetime = datetime.fromtimestamp(epoch, tz)

        # todo: save to rtc, and get time from rtc in the tick()


async def main(display):
    await uasyncio.gather(display.loop(), display.tick())

    # uasyncio.create_task(display.loop())
    # uasyncio.create_task(tick(display))
    # await uasyncio.sleep(100)

print("start")

display = Display()
# if do_connect():
#     for name, location in modules_to_install:
#         mip.install(location,  mpy=False)
#     #
#     # t = TimeHandler()
#     # buf = "{:02}{:02}".format(t.datetime.hour, t.datetime.minute)
#     # display.set(buf)
#     display.set(1337)
# else:
#     display.set("0000")

display.set("1337")
i2c = I2C(sda=Pin(0), scl=Pin(4))
ds = DS3231(i2c)

# scl  d2 4
# sda  d3 0

year = 2020 # Can be yyyy or yy format
month = 10
mday = 3
hour = 13 # 24 hour format only
minute = 55
second = 30 # Optional
weekday = 6 # Optional

dt = (year, month, mday, hour, minute, second, weekday)
a = ds.datetime(dt)
print(a)

# uasyncio.run(main(display))
print("stop")


