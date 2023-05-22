import uasyncio

from machine import Pin, SPI


class Digit:
    digits: list

    dot = False
    empty = False
    number = 0

    def __init__(self, y):
        self.digits = [
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

        self.set(y)

    def set(self, y):
        self.number = y
        return self.digits[y]

    def get(self):
        if self.dot:
            return self.digits[self.number] - 0b10000000
        if self.empty:
            # todo: empty
            return self.digits[self.number]

        return self.digits[self.number]

    def toggle_dot(self):
        self.dot = not self.dot


class Display:
    places = [8, 4, 2, 1]

    def __init__(self) -> None:
        self.spi = SPI(1, 10000000)
        self.rclk = Pin(5, Pin.OUT)

        self.digits = [Digit(0), Digit(0), Digit(0), Digit(0)]

    def set(self, numbs: int | str):
        # this whole set and get is stupid, but it's mvp
        if isinstance(numbs, str):
            assert numbs.isdigit()

        if int(numbs) > 9999:
            self.set(0)

        numbs = "{:04}".format(int(numbs))
        for n, d in zip(numbs, self.digits):
            d.set(int(n))

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

    async def animation(self, n, left_to_right=True):
        # this is stupid, i don't have time for this
        if left_to_right:
            buf = n * 1000
            for _ in self.digits:
                self.set(buf)
                buf /= 10
                await uasyncio.sleep_ms(500)
        else:
            buf = n
            for _ in self.digits:
                self.set(buf)
                buf *= 10
                await uasyncio.sleep_ms(500)


display = Display()

