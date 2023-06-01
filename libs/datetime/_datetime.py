
from libs.datetime.dt import _date, _time, _iso2d, _tmod, _o2ymd, _iso2t, _d2iso, _t2iso
from libs.datetime.timezone import timezone
from libs.datetime.timedelta import timedelta


class datetime:
    def __init__(
        self, year, month, day, hour=0, minute=0, second=0, microsecond=0, tzinfo=None, *, fold=0
    ):
        self._d = _date(year, month, day)
        self._t = _time(hour, minute, second, microsecond, fold)
        self._tz = tzinfo
        self._fd = fold

    @classmethod
    def fromtimestamp(cls, ts, tz=None):
        if isinstance(ts, float):
            ts, us = divmod(round(ts * 1_000_000), 1_000_000)
        else:
            us = 0
        if tz is None:
            raise NotImplementedError
        else:
            dt = cls(*_tmod.gmtime(ts)[:6], microsecond=us, tzinfo=tz)
            dt = tz.fromutc(dt)
        return dt

    @classmethod
    def now(cls, tz=None):
        return cls.fromtimestamp(_tmod.time(), tz)

    @classmethod
    def fromordinal(cls, n):
        return cls(0, 0, n)

    @classmethod
    def fromisoformat(cls, s):
        d = _iso2d(s)
        if len(s) <= 12:
            return cls(*d)
        t = _iso2t(s[11:])
        return cls(*(d + t))

    @classmethod
    def combine(cls, date, time, tzinfo=None):
        return cls(
            0, 0, date.toordinal(), 0, 0, 0, time._td._us, tzinfo or time._tz, fold=time._fd
        )

    @property
    def year(self):
        return _o2ymd(self._d)[0]

    @property
    def month(self):
        return _o2ymd(self._d)[1]

    @property
    def day(self):
        return _o2ymd(self._d)[2]

    @property
    def hour(self):
        return self._t.tuple()[1]

    @property
    def minute(self):
        return self._t.tuple()[2]

    @property
    def second(self):
        return self._t.tuple()[3]

    @property
    def microsecond(self):
        return self._t.tuple()[4]

    @property
    def tzinfo(self):
        return self._tz

    @property
    def fold(self):
        return self._fd

    def __add__(self, other):
        us = self._t._us + other._us
        d, us = divmod(us, 86_400_000_000)
        d += self._d
        return datetime(0, 0, d, 0, 0, 0, us, self._tz)

    def __sub__(self, other):
        if isinstance(other, timedelta):
            return self.__add__(-other)
        elif isinstance(other, datetime):
            d, us = self._sub(other)
            return timedelta(d, 0, us)
        else:
            raise TypeError

    def _sub(self, other):
        # Subtract two datetime instances.
        tz1 = self._tz
        if (tz1 is None) ^ (other._tz is None):
            raise TypeError
        dt1 = self
        dt2 = other
        if tz1 is not None:
            os1 = dt1.utcoffset()
            os2 = dt2.utcoffset()
            if os1 != os2:
                dt1 -= os1
                dt2 -= os2
        D = dt1._d - dt2._d
        us = dt1._t._us - dt2._t._us
        d, us = divmod(us, 86_400_000_000)
        return D + d, us

    def __eq__(self, other):
        if (self._tz == None) ^ (other._tz == None):
            return False
        return self._cmp(other) == 0

    def __le__(self, other):
        return self._cmp(other) <= 0

    def __lt__(self, other):
        return self._cmp(other) < 0

    def __ge__(self, other):
        return self._cmp(other) >= 0

    def __gt__(self, other):
        return self._cmp(other) > 0

    def _cmp(self, other):
        # Compare two datetime instances.
        d, us = self._sub(other)
        if d < 0:
            return -1
        if d > 0:
            return 1

        if us < 0:
            return -1
        if us > 0:
            return 1

        return 0

    def date(self):
        from datetime import date
        return date.fromordinal(self._d)

    def time(self):
        from datetime import time
        return time(microsecond=self._t._us, fold=self._fd)

    def timetz(self):
        from datetime import time
        return time(microsecond=self._t._us, tzinfo=self._tz, fold=self._fd)

    def replace(
        self,
        year=None,
        month=None,
        day=None,
        hour=None,
        minute=None,
        second=None,
        microsecond=None,
        tzinfo=True,
        *,
        fold=None,
    ):
        Y, M, D, h, m, s, us, tz, fl = self.tuple()
        if year is None:
            year = Y
        if month is None:
            month = M
        if day is None:
            day = D
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
        return datetime(year, month, day, hour, minute, second, microsecond, tzinfo, fold=fold)

    def astimezone(self, tz=None):
        if self._tz is tz:
            return self
        _tz = self._tz
        if _tz is None:
            raise NotImplementedError
        else:
            os = _tz.utcoffset(self)
        utc = self - os
        utc = utc.replace(tzinfo=tz)
        return tz.fromutc(utc)

    def utcoffset(self):
        return None if self._tz is None else self._tz.utcoffset(self)

    def dst(self):
        return None if self._tz is None else self._tz.dst(self)

    def tzname(self):
        return None if self._tz is None else self._tz.tzname(self)

    def timetuple(self):
        if self._tz is None:
            conv = _tmod.gmtime
            epoch = datetime.EPOCH.replace(tzinfo=None)
        else:
            conv = _tmod.localtime
            epoch = datetime.EPOCH
        return conv(round((self - epoch).total_seconds()))

    def toordinal(self):
        return self._d

    def timestamp(self):
        if self._tz is None:
            raise NotImplementedError
        else:
            return (self - datetime.EPOCH).total_seconds()

    def weekday(self):
        return (self._d + 6) % 7

    def isoweekday(self):
        return self._d % 7 or 7

    def isoformat(self, sep="T", timespec="auto"):
        return _d2iso(self._d) + sep + _t2iso(self._t, timespec, self, self._tz)

    def __repr__(self):
        Y, M, D, h, m, s, us, tz, fold = self.tuple()
        tz = repr(tz)
        return "datetime.datetime({}, {}, {}, {}, {}, {}, {}, {}, fold={})".format(
            Y, M, D, h, m, s, us, tz, fold
        )

    def __str__(self):
        return self.isoformat(" ")

    def __hash__(self):
        if not hasattr(self, "_hash"):
            self._hash = hash((self._d, self._t, self._tz))
        return self._hash

    def tuple(self):
        d = _o2ymd(self._d)
        t = self._t.tuple()[1:]
        return d + t + (self._tz, self._fd)


datetime.EPOCH = datetime(*_tmod.gmtime(0)[:6], tzinfo=timezone.utc)
