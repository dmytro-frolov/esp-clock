import asyncio
import datetime as stdlib_datetime
import importlib
import sys
import types
import unittest


class Pin:
    OUT = 1

    def __init__(self, number, mode=None):
        self.number = number
        self.mode = mode
        self.values = []

    def __call__(self, value):
        self.values.append(value)


class SPI:
    def __init__(self, bus, baudrate):
        self.bus = bus
        self.baudrate = baudrate
        self.writes = []

    def write(self, value):
        self.writes.append(bytes(value))


class I2C:
    def __init__(self, **kwargs):
        self.kwargs = kwargs


class DS3231:
    def __init__(self, i2c):
        self.i2c = i2c
        self.value = (2024, 6, 7, 4, 8, 9, 10, 0)

    def datetime(self, value=None):
        if value is not None:
            self.value = value
        return self.value


class RotaryIRQ:
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def value(self):
        return 1


class Task:
    def __init__(self, coroutine):
        coroutine.close()
        self.cancelled = False

    def cancel(self):
        self.cancelled = True


machine = types.ModuleType("machine")
machine.Pin = Pin
machine.SPI = SPI
machine.I2C = I2C
sys.modules["machine"] = machine
uasyncio = types.ModuleType("uasyncio")
uasyncio.create_task = Task


async def sleep_ms(_):
    pass


uasyncio.sleep_ms = sleep_ms
sys.modules["uasyncio"] = uasyncio

ds3231 = types.ModuleType("libs.ds3231")
ds3231.DS3231 = DS3231
sys.modules["libs.ds3231"] = ds3231
rotary_irq = types.ModuleType("libs.rotary_irq")
rotary_irq.RotaryIRQ = RotaryIRQ
sys.modules["libs.rotary_irq"] = rotary_irq
sys.modules["libs.datetime.datetime"] = stdlib_datetime
sys.modules["libs.datetime.timedelta"] = stdlib_datetime
sys.modules["libs.datetime.timezone"] = stdlib_datetime

display_module = importlib.import_module("display")
time_module = importlib.import_module("time_handler")
modes_module = importlib.import_module("modes")


class DigitTests(unittest.TestCase):
    def test_segments_and_decimal_dot(self):
        digit = display_module.Digit(8)

        self.assertEqual(digit.get(), 0b10000000)
        digit.toggle_dot()
        self.assertEqual(digit.get(), 0)

    def test_set_returns_segment_value(self):
        digit = display_module.Digit(0)

        self.assertEqual(digit.set("2"), 0b10100100)
        self.assertEqual(digit.number, "2")


class DisplayTests(unittest.TestCase):
    def setUp(self):
        self.display = display_module.Display()

    def test_set_and_get_four_digits(self):
        self.display.set("1234")

        self.assertEqual(self.display.get(), "1234")

    def test_invalid_length_blanks_display(self):
        self.display.set("123")

        self.assertEqual(self.display.get(), "    ")

    def test_clear_only_resets_decimal_dots(self):
        self.display.set("1234")
        for digit in self.display.digits:
            digit.dot = True

        self.display.clear()

        self.assertEqual(self.display.get(), "1234")
        self.assertFalse(any(digit.dot for digit in self.display.digits))

    def test_latch_pulses_output(self):
        self.display.latch()

        self.assertEqual(self.display.rclk.values, [1, 0])


class ModeTests(unittest.TestCase):
    def test_connect_uses_wifi_configuration(self):
        class WLAN:
            credentials = None

            def active(self, _):
                pass

            def isconnected(self):
                return self.credentials is not None

            def connect(self, ssid, password):
                self.credentials = (ssid, password)

            def ifconfig(self):
                return ("192.0.2.1", "255.255.255.0", "192.0.2.1", "192.0.2.1")

        wlan = WLAN()
        network = types.ModuleType("network")
        network.STA_IF = 0
        network.WLAN = lambda _: wlan
        sys.modules["network"] = network
        credentials = modes_module.WIFI_SSID, modes_module.WIFI_PASSWORD
        modes_module.WIFI_SSID = "test-network"
        modes_module.WIFI_PASSWORD = "test-password"
        try:
            self.assertTrue(modes_module.do_connect())
        finally:
            modes_module.WIFI_SSID, modes_module.WIFI_PASSWORD = credentials

        self.assertEqual(wlan.credentials, ("test-network", "test-password"))

    def test_encoder_values_map_to_four_modes(self):
        controller = modes_module.Mode()

        self.assertEqual([type(mode) for mode in controller.modes], [
            modes_module.Clock,
            modes_module.Date,
            modes_module.StopWatch,
            modes_module.HourStopWatch,
        ])
        self.assertEqual(controller.rotary.kwargs, {
            "pin_num_clk": 5,
            "pin_num_dt": 4,
            "min_val": 1,
            "max_val": 4,
            "reverse": True,
            "range_mode": 2,
        })

    def test_animation_moves_selected_mode_across_display(self):
        controller = modes_module.Mode()
        values = []
        original_set = modes_module.display.set
        modes_module.display.set = values.append
        try:
            asyncio.run(controller.animation(3))
        finally:
            modes_module.display.set = original_set

        self.assertEqual(values, ["3   ", " 3  ", "  3 ", "   3"])

    def test_listen_converts_encoder_value_to_zero_based_mode(self):
        class StopListening(Exception):
            pass

        class Rotary:
            values = iter((1, 4))

            def value(self):
                return next(self.values)

        controller = modes_module.Mode()
        controller.rotary = Rotary()
        calls = []

        async def animation(value):
            calls.append(("animation", value))

        async def set_mode(value):
            calls.append(("set", value))

        async def stop(_):
            raise StopListening

        controller.animation = animation
        controller.set = set_mode
        original_sleep_ms = modes_module.uasyncio.sleep_ms
        modes_module.uasyncio.sleep_ms = stop
        try:
            with self.assertRaises(StopListening):
                asyncio.run(controller.listen())
        finally:
            modes_module.uasyncio.sleep_ms = original_sleep_ms

        self.assertEqual(calls, [("animation", 4), ("set", 3)])

    def test_exit_cancels_and_forgets_tasks(self):
        mode = modes_module.Modes()
        tasks = [Task(modes_module.Clock().tick()), Task(modes_module.Clock().tick())]
        mode.tasks.extend(tasks)

        mode.exit()

        self.assertTrue(all(task.cancelled for task in tasks))
        self.assertEqual(mode.tasks, [])

    def test_switching_away_cancels_running_mode(self):
        controller = modes_module.Mode()
        asyncio.run(controller.set(2))
        stopwatch = controller.current_mode[1]
        task = stopwatch.tasks[0]

        asyncio.run(controller.set(3))

        self.assertTrue(task.cancelled)
        self.assertEqual(stopwatch.tasks, [])
        self.assertIsInstance(controller.current_mode[1], modes_module.HourStopWatch)


class TimeHandlerTests(unittest.TestCase):
    def setUp(self):
        self.handler = time_module.TimeHandler()

    def test_last_sunday(self):
        self.assertEqual(self.handler._last_sunday(2024, 3), 31)
        self.assertEqual(self.handler._last_sunday(2024, 10), 27)

    def test_dst_starts_at_0100_utc_on_last_sunday_in_march(self):
        before = (2024, 3, 31, 0, 59, 59)
        boundary = (2024, 3, 31, 1, 0, 0)

        self.assertEqual(self.handler._get_kyiv_timezone_offset(before), 2)
        self.assertEqual(self.handler._get_kyiv_timezone_offset(boundary), 3)

    def test_dst_ends_at_0100_utc_on_last_sunday_in_october(self):
        before = (2024, 10, 27, 0, 59, 59)
        boundary = (2024, 10, 27, 1, 0, 0)

        self.assertEqual(self.handler._get_kyiv_timezone_offset(before), 3)
        self.assertEqual(self.handler._get_kyiv_timezone_offset(boundary), 2)

    def test_set_writes_ds3231_tuple(self):
        self.handler.datetime = stdlib_datetime.datetime(2024, 6, 7, 8, 9, 10)

        result = self.handler.set()

        self.assertEqual(result, (2024, 6, 7, 8, 9, 10, 4))

    def test_get_converts_ds3231_tuple(self):
        self.handler.tz = stdlib_datetime.timezone(stdlib_datetime.timedelta(hours=3))
        self.handler.ds.value = (2024, 6, 7, 4, 8, 9, 10, 0)

        result = self.handler.get()

        self.assertEqual(result, stdlib_datetime.datetime(2024, 6, 7, 8, 9, 10,
                                                          tzinfo=self.handler.tz))

    def test_get_time_is_zero_padded(self):
        self.handler.ds.value = (2024, 6, 7, 4, 8, 9, 10, 0)

        self.assertEqual(self.handler.get_time(), "0809")

    def test_sync_stops_when_ntp_fails(self):
        self.handler._sync_ntp = lambda: False

        self.assertFalse(self.handler.sync())

    def test_sync_builds_local_datetime(self):
        self.handler.unixtime = 0
        self.handler.offset = 2
        self.handler._sync_ntp = lambda: True

        self.assertTrue(self.handler.sync())
        self.assertEqual(self.handler.datetime,
                         stdlib_datetime.datetime(1970, 1, 1, 2, 0,
                                                  tzinfo=stdlib_datetime.timezone(
                                                      stdlib_datetime.timedelta(hours=2))))


if __name__ == "__main__":
    unittest.main()
