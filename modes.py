try:
    from secrets import WIFI_PASSWORD, WIFI_SSID
except ImportError:
    WIFI_SSID = ""
    WIFI_PASSWORD = ""

import gc
import time
import uasyncio

from machine import Pin
from libs.rotary_irq import RotaryIRQ

from display import display
from time_handler import time_handler

gc.collect()


def do_connect():
    import network

    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    if not wlan.isconnected():
        print('connecting to network...')
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        for i in range(10):
            if wlan.isconnected():
                break
            print("Still connecting", "."*i)
            time.sleep(1)
        else:
            return False

    print('network config:', wlan.ifconfig())

    return wlan.isconnected()


class StopWatchState:
    max_ms = (100 * 60 * 60 - 1) * 1000

    def __init__(self):
        self.elapsed_ms = 0
        self.last_tick = None
        self.started = False
        self.paused = True

    def _update(self):
        if self.paused:
            return

        now = time.ticks_ms()
        elapsed = time.ticks_diff(now, self.last_tick)
        if elapsed > 0:
            self.elapsed_ms = min(self.max_ms, self.elapsed_ms + elapsed)
        self.last_tick = now

        if self.elapsed_ms == self.max_ms:
            self.paused = True

    def activate(self):
        if not self.started:
            self.started = True
            self.paused = False
            self.last_tick = time.ticks_ms()

    def pause(self):
        if self.started and not self.paused:
            self._update()
            self.paused = True

    def resume(self):
        if self.started and self.paused and self.elapsed_ms < self.max_ms:
            self.paused = False
            self.last_tick = time.ticks_ms()

    def toggle(self):
        if self.paused:
            self.resume()
        else:
            self.pause()

    def seconds(self):
        self._update()
        return self.elapsed_ms // 1000


class Mode:
    modes: list
    current_mode: tuple[int, "Modes"]

    def __init__(self):
        self.stopwatch = StopWatchState()
        self.modes = [Clock(), StopWatch(self.stopwatch),
                      HourStopWatch(self.stopwatch)]
        self.current_mode = (0, self.modes[0])
        self.rotary = RotaryIRQ(
            pin_num_clk=5,  # 10
            pin_num_dt=4,  # 9
            min_val=1,
            max_val=len(self.modes),
            reverse=True,
            range_mode=2)
        self.button = Pin(12, Pin.IN, Pin.PULL_UP)
        self.button_value = self.button.value()
        self.last_button_press = None

    async def get_time(self):
        if do_connect() and time_handler.sync():
            time_handler.set()

    async def set(self, n: int):
        self._pause_if_leaving(n)
        self.current_mode[1].exit()
        self.current_mode = (n, self.modes[n])

        await self.current_mode[1].run()

    def _pause_if_leaving(self, n):
        current = self.current_mode[1]
        target = self.modes[n]
        if isinstance(current, StopWatch) and not isinstance(target, StopWatch):
            self.stopwatch.pause()

    def check_button(self):
        value = self.button.value()
        now = time.ticks_ms()
        if (self.last_button_press is not None and
                time.ticks_diff(now, self.last_button_press) >= 200):
            self.last_button_press = None
        if self.button_value == 1 and value == 0:
            if (self.last_button_press is None and
                    isinstance(self.current_mode[1], StopWatch)):
                self.stopwatch.toggle()
                self.last_button_press = now
        self.button_value = value

    async def animation(self, n):
        self.current_mode[1].exit()
        display.clear()

        buf = n * 1000
        for _ in display.digits:
            display.set("{:4}".format(buf).replace("0", " "))
            buf //= 10
            await uasyncio.sleep_ms(180)

    async def listen(self):
        val_old = self.rotary.value()
        while True:
            val_new = self.rotary.value()
            if val_old != val_new:
                val_old = val_new

                self._pause_if_leaving(val_new - 1)
                await self.animation(val_new)
                await self.set(val_new - 1)

            self.check_button()
            await uasyncio.sleep_ms(50)


class Modes:
    tasks = None

    def __init__(self):
        self.tasks = []

    def run(self):
        raise NotImplementedError()

    def exit(self):
        for task in self.tasks:
            task.cancel()
        self.tasks.clear()


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
    def __init__(self, state):
        super().__init__()
        self.state = state

    async def run(self):
        self.state.activate()
        await super().run()

    def format_time(self, seconds):
        return "{:02}{:02}".format((seconds // 60) % 60, seconds % 60)

    async def tick(self):
        while True:
            seconds = self.state.seconds()
            if self.state.paused:
                display.digits[1].dot = True
            else:
                display.digits[1].toggle_dot()

            display.set(self.format_time(seconds))
            await uasyncio.sleep(1)


class HourStopWatch(StopWatch):
    def format_time(self, seconds):
        return "{:02}{:02}".format((seconds // 3600) % 100,
                                    (seconds // 60) % 60)


mode = Mode()
