import uasyncio


from time_handler import TimeHandler
from display import Display

modules_to_install = []



# EPOCH_FIX = 946677600

# try:
#     from datetime import datetime
# except ImportError:
#     modules_to_install.append(("datetime",
#                               "https://raw.githubusercontent.com/micropython/micropython-lib/master/python-stdlib/datetime/datetime.py"))
#


async def connect(t, d):
    if do_connect():
        d.set("1337")
        # await uasyncio.sleep(6)
        # t.get_from_interwebs()
        # t.set()


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


async def tick(display, t):
    while True:
        display.set(t.get_time())
        display.digits[1].toggle_dot()

        await uasyncio.sleep(1)


async def main():
    display = Display()
    t = TimeHandler()

    # await connect(t, display)
    # uasyncio.create_task(connect(t, display))

    # task = uasyncio.create_task(tick(display, t))
    # m = Mode(display, task)

    await uasyncio.gather(display.loop(), tick(display, t))

    # await uasyncio.gather(display.loop(), m.set(1))#, tick(display, t))



#     for name, location in modules_to_install:
#         mip.install(location,  mpy=False)

uasyncio.run(main())

