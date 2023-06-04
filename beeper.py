import machine

beeper = machine.Pin(15, machine.Pin.OUT)


def beep():
    beeper(1)
    beeper(0)
