import uasyncio

from libs.rotary_irq import RotaryIRQ

from display import display
from time_handler import time_handler
from buttons import button
from beeper import beep, beeper


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
        self.modes = [Clock(), Date(), StopWatch(), HourStopWatch()]
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

    def __init__(self):
        self.tasks = []

    def run(self):
        raise NotImplementedError()

    def exit(self):
        # if self.tasks:
        for task in self.tasks:
            task.cancel()


class Clock(Modes):
    async def run(self):
        self.tasks.append(uasyncio.create_task(self.tick()))

    def exit(self):
        super().exit()
        display.clear()

    async def tick(self):
        while True:
            dt = time_handler.get()
            display.set("{:02}{:02}".format(dt.hour, dt.minute))
            display.digits[1].toggle_dot()

            await uasyncio.sleep(1)


class StopWatch(Clock):
    time_format = "{3}{4}{6}{7}"  # mmss

    def __init__(self):
        super().__init__()
        now = time_handler.get()
        none_delta = now - now

        self.start_time = now
        self.time_delta = none_delta
        self.skipped_time = none_delta
        self.pause = False

    async def run(self):
        await super().run()
        self.tasks.append(uasyncio.create_task(self.get_pause()))

    async def tick(self):
        while True:
            if self.pause:
                display.digits[1].dot = True
                self.skipped_time = time_handler.get() - self.start_time - self.time_delta

            else:
                self.time_delta = time_handler.get() - self.start_time - self.skipped_time
                display.digits[1].toggle_dot()

            display.set(self.time_format.format(*self.time_delta.isoformat()))
            await uasyncio.sleep(1)

    async def get_pause(self):
        while True:
            if not button.value():
                self.pause = not self.pause
                await beep()

            await uasyncio.sleep_ms(1)


class HourStopWatch(StopWatch):
    time_format = "{0}{1}{3}{4}"  # hhmm


class Date(Modes):
    async def run(self):
        dt = time_handler.get()
        display.digits[1].dot = True
        display.set("{:02}{:02}".format(dt.day, dt.month))


mode = Mode()
