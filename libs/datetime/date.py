from libs.datetime.timedelta import timedelta
from libs.datetime.dt import _date, _tmod, _dbm, _d2iso, _o2ymd, _iso2d


class date:
    def __init__(self, year, month, day):
        self._ord = _date(year, month, day)

    @classmethod
    def fromtimestamp(cls, ts):
        return cls(*_tmod.localtime(ts)[:3])

    @classmethod
    def today(cls):
        return cls(*_tmod.localtime()[:3])

    @classmethod
    def fromordinal(cls, n):
        return cls(0, 0, n)

    @classmethod
    def fromisoformat(cls, s):
        return cls(*_iso2d(s))

    @property
    def year(self):
        return self.tuple()[0]

    @property
    def month(self):
        return self.tuple()[1]

    @property
    def day(self):
        return self.tuple()[2]

    def toordinal(self):
        return self._ord

    def timetuple(self):
        y, m, d = self.tuple()
        yday = _dbm(y, m) + d
        return (y, m, d, 0, 0, 0, self.weekday(), yday, -1)

    def replace(self, year=None, month=None, day=None):
        year_, month_, day_ = self.tuple()
        if year is None:
            year = year_
        if month is None:
            month = month_
        if day is None:
            day = day_
        return date(year, month, day)

    def __add__(self, other):
        return date.fromordinal(self._ord + other.days)

    def __sub__(self, other):
        if isinstance(other, date):
            return timedelta(days=self._ord - other._ord)
        else:
            return date.fromordinal(self._ord - other.days)

    def __eq__(self, other):
        if isinstance(other, date):
            return self._ord == other._ord
        else:
            return False

    def __le__(self, other):
        return self._ord <= other._ord

    def __lt__(self, other):
        return self._ord < other._ord

    def __ge__(self, other):
        return self._ord >= other._ord

    def __gt__(self, other):
        return self._ord > other._ord

    def weekday(self):
        return (self._ord + 6) % 7

    def isoweekday(self):
        return self._ord % 7 or 7

    def isoformat(self):
        return _d2iso(self._ord)

    def __repr__(self):
        return "datetime.date(0, 0, {})".format(self._ord)

    __str__ = isoformat

    def __hash__(self):
        if not hasattr(self, "_hash"):
            self._hash = hash(self._ord)
        return self._hash

    def tuple(self):
        return _o2ymd(self._ord)

MINYEAR = 1
MAXYEAR = 9_999

date.min = date(MINYEAR, 1, 1)
date.max = date(MAXYEAR, 12, 31)
date.resolution = timedelta(days=1)

