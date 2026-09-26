import gc
import uasyncio

from modes import mode, do_connect
from display import display


async def main():
    await mode.set(0)
    await uasyncio.gather(display.loop(), mode.listen())

uasyncio.run(mode.get_time())
gc.collect()
free_heap = gc.mem_free()
print("Free heap before main:", free_heap)
if free_heap < 5000:
    print("WARNING: low heap")
uasyncio.run(main())
