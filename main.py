import uasyncio

from modes import mode, do_connect
from display import display


async def main():
    await mode.set(0)
    await uasyncio.gather(display.loop(), mode.listen())

do_connect()
uasyncio.run(mode.get_time())
uasyncio.run(main())
