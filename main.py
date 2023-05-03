import time
from machine import Pin, SPI


class Display:
    number = [
        0b11000000, 
        0b11111001, 
        0b10100100, 
        0b10110000, 
        0b10011001,
        0b10010010, 
        0b10000010, 
        0b11111000, 
        0b10000000, 
        0b10010000,
    ]

    places = [8, 4, 2, 1]
    numbs = []

    def __init__(self) -> None:
        self.spi = SPI(1, 10000000)
        self.clr = Pin(16, Pin.OUT)
        self.rclk = Pin(5, Pin.OUT)

        self.set("4337")

    def set(self, numbs: str):
        assert len(numbs) == 4

        self.numbs = [self.number[int(n)] for n in numbs]

    def latch(self):
        self.rclk(1)
        self.rclk(0)

    def loop(self):
        self.clr(1)
        buf = bytearray(2)

        while True:
            for place, numb in zip(self.places, self.numbs):
                buf[0] = numb
                buf[1] = place

                self.spi.write(buf)
                self.latch()


display = Display()
display.loop()


