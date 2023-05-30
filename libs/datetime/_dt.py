# datetime.py
# from https://github.com/micropython/micropython-lib/blob/master/python-stdlib/datetime/datetime.py

import time as _tmod

__version__ = "2.0.0"

_DBM = (0, 0, 31, 59, 90, 120, 151, 181, 212, 243, 273, 304, 334)
_DIM = (0, 31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31)
_TIME_SPEC = ("auto", "hours", "minutes", "seconds", "milliseconds", "microseconds")

from libs.datetime.timedelta import timedelta
from libs.datetime.timezone import timezone


def _leap(y):
    return y % 4 == 0 and (y % 100 != 0 or y % 400 == 0)


def _dby(y):
    # year -> number of days before January 1st of year.
    Y = y - 1
    return Y * 365 + Y // 4 - Y // 100 + Y // 400


def _dim(y, m):
    # year, month -> number of days in that month in that year.
    if m == 2 and _leap(y):
        return 29
    return _DIM[m]


def _dbm(y, m):
    # year, month -> number of days in year preceding first day of month.
    return _DBM[m] + (m > 2 and _leap(y))


def _ymd2o(y, m, d):
    # y, month, day -> ordinal, considering 01-Jan-0001 as day 1.
    return _dby(y) + _dbm(y, m) + d


def _o2ymd(n):
    # ordinal -> (year, month, day), considering 01-Jan-0001 as day 1.
    n -= 1
    n400, n = divmod(n, 146_097)
    y = n400 * 400 + 1
    n100, n = divmod(n, 36_524)
    n4, n = divmod(n, 1_461)
    n1, n = divmod(n, 365)
    y += n100 * 100 + n4 * 4 + n1
    if n1 == 4 or n100 == 4:
        return y - 1, 12, 31
    m = (n + 50) >> 5
    prec = _dbm(y, m)
    if prec > n:
        m -= 1
        prec -= _dim(y, m)
    n -= prec
    return y, m, n + 1


MINYEAR = 1
MAXYEAR = 9_999


def _date(y, m, d):
    if MINYEAR <= y <= MAXYEAR and 1 <= m <= 12 and 1 <= d <= _dim(y, m):
        return _ymd2o(y, m, d)
    elif y == 0 and m == 0 and 1 <= d <= 3_652_059:
        return d
    else:
        raise ValueError


def _iso2d(s):  # ISO -> date
    if len(s) < 10 or s[4] != "-" or s[7] != "-":
        raise ValueError
    return int(s[0:4]), int(s[5:7]), int(s[8:10])


def _d2iso(o):  # date -> ISO
    return "%04d-%02d-%02d" % _o2ymd(o)



def _time(h, m, s, us, fold):
    if (
        0 <= h < 24
        and 0 <= m < 60
        and 0 <= s < 60
        and 0 <= us < 1_000_000
        and (fold == 0 or fold == 1)
    ) or (h == 0 and m == 0 and s == 0 and 0 < us < 86_400_000_000):
        return timedelta(0, s, us, 0, m, h)
    else:
        raise ValueError


def _iso2t(s):
    hour = 0
    minute = 0
    sec = 0
    usec = 0
    tz_sign = ""
    tz_hour = 0
    tz_minute = 0
    tz_sec = 0
    tz_usec = 0
    l = len(s)
    i = 0
    if l < 2:
        raise ValueError
    i += 2
    hour = int(s[i - 2 : i])
    if l > i and s[i] == ":":
        i += 3
        if l - i < 0:
            raise ValueError
        minute = int(s[i - 2 : i])
        if l > i and s[i] == ":":
            i += 3
            if l - i < 0:
                raise ValueError
            sec = int(s[i - 2 : i])
            if l > i and s[i] == ".":
                i += 4
                if l - i < 0:
                    raise ValueError
                usec = 1000 * int(s[i - 3 : i])
                if l > i and s[i] != "+":
                    i += 3
                    if l - i < 0:
                        raise ValueError
                    usec += int(s[i - 3 : i])
    if l > i:
        if s[i] not in "+-":
            raise ValueError
        tz_sign = s[i]
        i += 6
        if l - i < 0:
            raise ValueError
        tz_hour = int(s[i - 5 : i - 3])
        tz_minute = int(s[i - 2 : i])
        if l > i and s[i] == ":":
            i += 3
            if l - i < 0:
                raise ValueError
            tz_sec = int(s[i - 2 : i])
            if l > i and s[i] == ".":
                i += 7
                if l - i < 0:
                    raise ValueError
                tz_usec = int(s[i - 6 : i])
    if l != i:
        raise ValueError
    if tz_sign:
        td = timedelta(hours=tz_hour, minutes=tz_minute, seconds=tz_sec, microseconds=tz_usec)
        if tz_sign == "-":
            td = -td
        tz = timezone(td)
    else:
        tz = None
    return hour, minute, sec, usec, tz


def _t2iso(td, timespec, dt, tz):
    s = td._format(_TIME_SPEC.index(timespec))
    if tz is not None:
        s += tz.isoformat(dt)
    return s


