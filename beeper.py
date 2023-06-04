import machine
import uasyncio

beeper = machine.Pin(15, machine.Pin.OUT)


async def beep():
    beeper(1)
    await uasyncio.sleep_ms(10)
    beeper(0)
