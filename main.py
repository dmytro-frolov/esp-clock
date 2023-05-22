# from libs.datetime import datetime
# from libs.datetime import timezone
# from libs.datetime import timedelta


#
import uasyncio

from time_handler import time_handler
from modes import mode
from display import display


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


async def connect():
    if do_connect():
        time_handler.sync()
        time_handler.set()


async def main():
    # mode.set(0)

    await uasyncio.gather(display.loop(), mode.listen())

    # display = Display()
    # time_handler = TimeHandler()

    # looks like it's not async
    # uasyncio.create_task(connect(time_handler))
    # await uasyncio.gather(display.loop(), tick(display, time_handler))

    # await uasyncio.gather(display.loop(), m.set(1))#, tick(display, t))



#     for name, location in modules_to_install:
#         mip.install(location,  mpy=False)

uasyncio.run(main())

