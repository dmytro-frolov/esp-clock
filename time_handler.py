from machine import Pin, I2C

from libs.datetime import datetime
from libs.datetime import timezone
from libs.datetime import timedelta
from libs.ds3231 import DS3231


class TimeHandler:
    offset = 0

    def _last_sunday(self, year, month):
        day = 31
        while day > 24:
            if datetime.datetime(year, month, day).weekday() == 6:
                return day
            day -= 1

        raise ValueError("Failed to find last Sunday")

    def _get_kyiv_timezone_offset(self, utc_dt):
        # Europe/Kyiv uses UTC+2 in winter and UTC+3 in summer.
        # DST starts on the last Sunday of March at 03:00 local standard time,
        # which is 01:00 UTC. DST ends on the last Sunday of October at
        # 04:00 local daylight time, which is also 01:00 UTC.
        year = utc_dt[0]
        current_utc = datetime.datetime(*utc_dt[:6])

        march_day = self._last_sunday(year, 3)
        october_day = self._last_sunday(year, 10)

        dst_start_utc = datetime.datetime(year, 3, march_day, 1, 0, 0)
        dst_end_utc = datetime.datetime(year, 10, october_day, 1, 0, 0)

        is_dst = dst_start_utc <= current_utc < dst_end_utc
        offset = 3 if is_dst else 2

        return offset

    def _sync_ntp(self):
        import time

        try:
            import ntptime
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
        if not self._sync_ntp():
            return False

        print(f"Got time from NTP: unixtime={self.unixtime}, offset={self.offset}")

        delta = timedelta.timedelta(hours=self.offset)
        self.tz = timezone.timezone(delta)

        self.datetime = datetime.datetime.fromtimestamp(self.unixtime, self.tz)
        return True

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
