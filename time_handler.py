from machine import Pin, I2C

from libs.datetime import datetime
from libs.datetime import timezone
from libs.datetime import timedelta
from libs.ds3231 import DS3231


# todo: use timedelta for this
# some embedded ports use epoch of 2000-01-01 00:00:00 UTC
if datetime._tmod.gmtime(0)[0] == 2000:
    EPOCH_FIX = 946684800 # check
else:
    EPOCH_FIX = 0


class TimeHandler:
    offset = 0

    def _get_kyiv_timezone_offset(self, dt):
        # Kyiv is in EET (UTC+2) or EEST (UTC+3, DST)
        # DST in Ukraine starts last Sunday of March at 3:00 and ends last Sunday of October at 4:00
        print(f"Calculating DST for year: {dt[0]}")
        year = dt[0]
        # Find last Sunday of March
        last_march = 31
        for _ in range(31):
            if datetime.datetime(year, 3, last_march).weekday() == 6:  # Sunday
                dst_start = datetime.datetime(year, 3, last_march, 3, 0, 0)
                break
            last_march -= 1

        # Find last Sunday of October
        last_october = 31
        for _ in range(31):
            if datetime.datetime(year, 10, last_october).weekday() == 6:  # Sunday
                dst_end = datetime.datetime(year, 10, last_october, 4, 0, 0)
                break
            last_october -= 1

        current_dt = datetime.datetime(*dt[:6])

        # Check if current time is in DST
        is_dst = dst_start <= current_dt < dst_end
        offset = 3 if is_dst else 2
        print(f"Current time: {current_dt}")
        print(f"DST period: {dst_start} to {dst_end}")
        print(f"Is DST: {is_dst}, Using offset: {offset} hours")
        return offset

    def _get_from_std_lib(self):
        import time

        try:
            import ntptime
            ntptime.settime()
            self.unixtime = ntptime.time()
            print(f"NTP time received: {self.unixtime}")

        except OSError:
            print("LIB: ntptime error")
            return False

        utc_time = time.gmtime(self.unixtime)
        self.offset = self._get_kyiv_timezone_offset(utc_time)
        return True

    def __init__(self):
        i2c = I2C(sda=Pin(0), scl=Pin(2))
        self.ds = DS3231(i2c)

        delta = timedelta.timedelta(hours=0)
        self.tz = timezone.timezone(delta)

    def sync(self):
        print("Syncing time...")
        if not self._get_from_std_lib():
            return

        print(f"Got time from NTP: unixtime={self.unixtime}, offset={self.offset}")

        delta = timedelta.timedelta(hours=self.offset)
        self.tz = timezone.timezone(delta)

        self.datetime = datetime.datetime.fromtimestamp(self.unixtime, self.tz)

    def set(self):
        return self.ds.datetime(
            (self.datetime.year, self.datetime.month, self.datetime.day,
             self.datetime.hour, self.datetime.minute, self.datetime.second,
             self.datetime.weekday())
        )

    def get(self): # rename to now()
        # todo: return with timezone. does not work properly
        buf_dt = list(self.ds.datetime())
        del buf_dt[3]
        return datetime.datetime(*buf_dt, tzinfo=self.tz)

    def get_time(self) -> str:
        dt = self.ds.datetime()
        return "{:02}{:02}".format(dt[4], dt[5])


time_handler = TimeHandler()
