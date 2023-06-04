import uasyncio

from machine import Pin, SPI


class Digit:
    digits: dict

    dot = False
    number = " "

    def __init__(self, y):
        self.digits = {
            " ": 0b11111111,
            "0": 0b11000000,
            "1": 0b11111001,
            "2": 0b10100100,
            "3": 0b10110000,
            "4": 0b10011001,
            "5": 0b10010010,
            "6": 0b10000010,
            "7": 0b11111000,
            "8": 0b10000000,
            "9": 0b10010000,
        }

        self.set(str(y))

    def set(self, y):
        self.number = y
        return self.digits[y]

    def get(self):
        if self.dot:
            return self.digits[self.number] - 0b10000000

        return self.digits[self.number]

    def toggle_dot(self):
        self.dot = not self.dot


class Display:
    places = [8, 4, 2, 1]

    def __init__(self) -> None:
        self.spi = SPI(1, 10000000)
        self.rclk = Pin(16, Pin.OUT)

        self.digits = [Digit(0), Digit(0), Digit(0), Digit(0)]

    def set(self, numbs: str):
        if len(numbs) != len(self.digits):
            numbs = " " * len(self.digits)

        for n, d in zip(numbs, self.digits):
            d.set(n)

    def get(self) -> str:
        return "".join([str(d.number) for d in self.digits])

    def clear(self):
        for digit in self.digits:
            digit.dot = False

    def latch(self):
        self.rclk(1)
        self.rclk(0)

    async def loop(self):
        buf = bytearray(2)

        while True:
            for place, digit in zip(self.places, self.digits):
                buf[0] = digit.get()
                buf[1] = place

                self.spi.write(buf)
                self.latch()

                await uasyncio.sleep_ms(1)

display = Display()
