import machine

# pin 15 must be in the air before flashing
button = machine.Pin(15, machine.Pin.IN, machine.Pin.PULL_UP)

