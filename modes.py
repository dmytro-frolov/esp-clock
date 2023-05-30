import uasyncio

from libs.rotary_irq import RotaryIRQ

from display import display
from time_handler import time_handler


def do_connect():
    import network

    # wlan.config(dhcp_hostname="foo-bar-baz")

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('connecting to network...')
        wlan.connect("()", "")  # connect to an AP
        while not wlan.isconnected():
            pass
    print('network config:', wlan.ifconfig())

    return wlan.isconnected()


class Mode:
    modes: list
    current_mode: tuple[int, "Modes"]

    def __init__(self):
        self.modes = [Clock(), Leet(), Bond(), StopWatch()]
        self.current_mode = (0, self.modes[0])
        self.rotary = RotaryIRQ(
            pin_num_clk=5,  # 10
            pin_num_dt=4,  # 9
            min_val=1,
            max_val=len(self.modes),
            reverse=True,
            range_mode=2)

    async def get_time(self):
        if do_connect():
            time_handler.sync()
            time_handler.set()

    async def set(self, n: int):
        self.current_mode[1].exit()
        self.current_mode = (n, self.modes[n])

        await self.current_mode[1].run()

    async def animation(self, n):
        self.current_mode[1].exit()
        buf = n * 1000
        for _ in display.digits:
            display.set(buf)
            buf /= 10
            await uasyncio.sleep_ms(180)

    async def listen(self):
        val_old = self.rotary.value()
        while True:
            val_new = self.rotary.value()
            if val_old != val_new:
                val_old = val_new

                await self.animation(val_new)
                await self.set(val_new - 1)

            await uasyncio.sleep_ms(50)


class Modes:
    tasks = None

    def run(self):
        raise NotImplementedError()

    def exit(self):
        if self.tasks:
            self.tasks.cancel()


class Clock(Modes):
    async def run(self):
        display.set(self._get_time())
        self.tasks = uasyncio.create_task(self.tick())

    def exit(self):
        super().exit()
        display.clear()

    def _get_time(self):
        dt = time_handler.get()
        return "{:02}{:02}".format(dt.hour, dt.minute)

    async def tick(self):
        while True:
            display.set(self._get_time())
            display.digits[1].toggle_dot()

            # await uasyncio.sleep(1)
            await uasyncio.sleep_ms(40)


class StopWatch(Clock):
    def __init__(self):
        self.start_time = time_handler.get()

    def _get_time(self):
        # todo: fix here
        time_delta = time_handler.get() - self.start_time
        # return "{3}{4}{6}{7}".format(*time_delta.isoformat())  # mmss
        return "{0}{1}{3}{4}".format(*time_delta.isoformat())  # hhmm


class Leet(Modes):
    async def run(self):
        display.set("1337")


class Bond(Modes):
    async def run(self):
        display.set("0007")


class Date(Modes):
    pass


mode = Mode()
