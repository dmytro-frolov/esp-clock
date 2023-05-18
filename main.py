# from libs.datetime import datetime
# from libs.datetime import timezone
# from libs.datetime import timedelta


#
import uasyncio

from time_handler import TimeHandler
from display import Display


def do_connect():
    import network

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('connecting to network...')
        wlan.connect("()", "")  # connect to an AP
        while not wlan.isconnected():
            pass
    print('network config:', wlan.ifconfig())

    return wlan.isconnected()


async def connect(time_handler):
    if do_connect():
        time_handler.sync()
        time_handler.set()


class Mode:
    def __init__(self, display: Display, tick_task):
        self.display = display
        self.tick_task = tick_task

    async def set(self, n: int):
        await uasyncio.sleep(1)
        self.tick_task.cancel()

        # self.display.clear()
        await self.animation(n, left_to_right=False)
        await uasyncio.sleep(3)

    async def animation(self, n, left_to_right=True):
        # this is stupid, i don't have time for this
        if left_to_right:
            buf = n * 1000
            for _ in self.display.digits:
                self.display.set(buf)
                buf /= 10
                await uasyncio.sleep_ms(500)
        else:
            buf = n
            for _ in self.display.digits:
                self.display.set(buf)
                buf *= 10
                await uasyncio.sleep_ms(500)

    async def listen(self):
        while True:
            pass
            # going to listen for input


async def tick(display, t):
    while True:
        display.set(t.get_time())
        display.digits[1].toggle_dot()

        await uasyncio.sleep(1)


async def main():
    display = Display()
    time_handler = TimeHandler()

    uasyncio.create_task(connect(time_handler))
    await uasyncio.gather(display.loop(), tick(display, time_handler))

    # await uasyncio.gather(display.loop(), m.set(1))#, tick(display, t))



#     for name, location in modules_to_install:
#         mip.install(location,  mpy=False)

uasyncio.run(main())

