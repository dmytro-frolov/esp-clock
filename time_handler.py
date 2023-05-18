from machine import Pin, I2C

from libs.datetime import datetime
from libs.datetime import timezone
from libs.datetime import timedelta
from libs import DS3231


# todo: use timedelta for this
# some embedded ports use epoch of 2000-01-01 00:00:00 UTC
if datetime._tmod.gmtime(0)[0] == 2000:
    EPOCH_FIX = 946684800 # check
else:
    EPOCH_FIX = 0


class TimeHandler:
    offset = 0

    def _get_from_worldtimeapi(self):
        import urequests

        resp = urequests.get("http://worldtimeapi.org/api/ip")
        if resp.status_code == 200:
            resp = resp.json()
            # todo: offset with minutes
            self.offset = int(resp["utc_offset"].split(':')[0])
            self.unixtime = resp["unixtime"]

        else:
            raise Exception(f"Status code: {resp.status_code}")

    def _get_from_std_lib(self):
        import ntptime

        self.offset = 0
        self.unixtime = ntptime.settime()

    def __init__(self):
        # scl  d2 4
        # sda  d3 0
        i2c = I2C(sda=Pin(0), scl=Pin(4))
        self.ds = DS3231(i2c)

    def sync(self):
        try:
            self._get_from_worldtimeapi()
        except Exception:
            self._get_from_std_lib()
        else:
            self.unixtime -= EPOCH_FIX

        delta = timedelta.timedelta(hours=self.offset)
        self.tz = timezone.timezone(delta)

        self.datetime = datetime.datetime.fromtimestamp(self.unixtime, self.tz)

    def set(self):
        return self.ds.datetime(
            (self.datetime.year, self.datetime.month, self.datetime.day,
             self.datetime.hour, self.datetime.minute, self.datetime.second,
             self.datetime.weekday())
        )

    def get(self):
        # todo: return with timezone. does not work properly
        return datetime.datetime(*self.ds.datetime())

    def get_time(self) -> str:
        dt = self.ds.datetime()
        return "{:02}{:02}".format(dt[4], dt[5])

