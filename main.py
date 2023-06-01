import uasyncio

from modes import mode
from display import display


async def main():
    await mode.set(0)
    await uasyncio.gather(display.loop(), mode.listen())


uasyncio.run(main())
