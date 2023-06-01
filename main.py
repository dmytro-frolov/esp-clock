import uasyncio

from modes import mode
from display import display

# from time_handler import time_handler
# st = time_handler.get()
#

async def main():
    await mode.set(0)
    await uasyncio.gather(display.loop(), mode.listen())


uasyncio.run(main())
