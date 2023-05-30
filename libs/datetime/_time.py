from libs.datetime.timedelta import timedelta

from libs.datetime.dt import _time, _iso2t, _t2iso


class time:
    def __init__(self, hour=0, minute=0, second=0, microsecond=0, tzinfo=None, *, fold=0):
        self._td = _time(hour, minute, second, microsecond, fold)
        self._tz = tzinfo
        self._fd = fold

    @classmethod
    def fromisoformat(cls, s):
        return cls(*_iso2t(s))

    @property
    def hour(self):
        return self.tuple()[0]

    @property
    def minute(self):
        return self.tuple()[1]

    @property
    def second(self):
        return self.tuple()[2]

    @property
    def microsecond(self):
        return self.tuple()[3]

    @property
    def tzinfo(self):
        return self._tz

    @property
    def fold(self):
        return self._fd

    def replace(
        self, hour=None, minute=None, second=None, microsecond=None, tzinfo=True, *, fold=None
    ):
        h, m, s, us, tz, fl = self.tuple()
        if hour is None:
            hour = h
        if minute is None:
            minute = m
        if second is None:
            second = s
        if microsecond is None:
            microsecond = us
        if tzinfo is True:
            tzinfo = tz
        if fold is None:
            fold = fl
        return time(hour, minute, second, microsecond, tzinfo, fold=fold)

    def isoformat(self, timespec="auto"):
        return _t2iso(self._td, timespec, None, self._tz)

    def __repr__(self):
        return "datetime.time(microsecond={}, tzinfo={}, fold={})".format(
            self._td._us, repr(self._tz), self._fd
        )

    __str__ = isoformat

    def __bool__(self):
        return True

    def __eq__(self, other):
        if (self._tz == None) ^ (other._tz == None):
            return False
        return self._sub(other) == 0

    def __le__(self, other):
        return self._sub(other) <= 0

    def __lt__(self, other):
        return self._sub(other) < 0

    def __ge__(self, other):
        return self._sub(other) >= 0

    def __gt__(self, other):
        return self._sub(other) > 0

    def _sub(self, other):
        tz1 = self._tz
        if (tz1 is None) ^ (other._tz is None):
            raise TypeError
        us1 = self._td._us
        us2 = other._td._us
        if tz1 is not None:
            os1 = self.utcoffset()._us
            os2 = other.utcoffset()._us
            if os1 != os2:
                us1 -= os1
                us2 -= os2
        return us1 - us2

    def __hash__(self):
        if not hasattr(self, "_hash"):
            # fold doesn't make any difference
            self._hash = hash((self._td, self._tz))
        return self._hash

    def utcoffset(self):
        return None if self._tz is None else self._tz.utcoffset(None)

    def dst(self):
        return None if self._tz is None else self._tz.dst(None)

    def tzname(self):
        return None if self._tz is None else self._tz.tzname(None)

    def tuple(self):
        d, h, m, s, us = self._td.tuple()
        return h, m, s, us, self._tz, self._fd


time.min = time(0)
time.max = time(23, 59, 59, 999_999)
time.resolution = timedelta.resolution


