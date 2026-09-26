import gc
import uasyncio

from display import display
from modes import mode


async def main():
    display.set("----")
    uasyncio.create_task(display.loop())
    await uasyncio.sleep_ms(0)
    await mode.get_time()
    await mode.set(0)

    gc.collect()
    free_heap = gc.mem_free()
    print("Free heap before main:", free_heap)
    if free_heap < 2500:
        print("WARNING: low heap")

    await mode.listen()

uasyncio.run(main())
