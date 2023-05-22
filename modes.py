import uasyncio

from display import display
from time_handler import time_handler


class Mode:
    modes: list
    current_mode: tuple[int, "Modes"]

    def __init__(self):
        self.modes = [Clock(), Leet()]
        self.current_mode = (1, self.modes[1])

    async def set(self, n: int):
        self.current_mode[1].exit()
        self.current_mode = (n, self.modes[n])

        await self.current_mode[1].run()

        # await self.animation(n, left_to_right=False)

    async def animation(self, n, left_to_right=True):
        # this is stupid, i don't have time for this
        if left_to_right:
            buf = n * 1000
            for _ in display.digits:
                display.set(buf)
                buf /= 10
                await uasyncio.sleep_ms(500)
        else:
            buf = n
            for _ in display.digits:
                display.set(buf)
                buf *= 10
                await uasyncio.sleep_ms(500)

    async def listen(self):
        while True:
            # await uasyncio.sleep(3)
            await self.set(0)

            await uasyncio.sleep(5)
            await self.set(1)

            await uasyncio.sleep(5)


            # going to listen for input


class Modes:
    tasks = None

    def run(self):
        raise NotImplementedError()

    def exit(self):
        if self.tasks:
            self.tasks.cancel()


class Clock(Modes):
    async def run(self):
        display.set(time_handler.get_time())
        self.tasks = uasyncio.create_task(self.tick())

    def exit(self):
        super().exit()
        display.clear()

    async def tick(self):
        while True:
            display.set(time_handler.get_time())
            display.digits[1].toggle_dot()

            await uasyncio.sleep(1)


class Leet(Modes):
    async def run(self):
        display.set("1337")


mode = Mode()
