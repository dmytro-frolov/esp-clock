from libs.datetime import datetime


class timedelta:
    def __init__(
        self, days=0, seconds=0, microseconds=0, milliseconds=0, minutes=0, hours=0, weeks=0
    ):
        s = (((weeks * 7 + days) * 24 + hours) * 60 + minutes) * 60 + seconds
        self._us = round((s * 1000 + milliseconds) * 1000 + microseconds)

    def __repr__(self):
        return "datetime.timedelta(microseconds={})".format(self._us)

    def total_seconds(self):
        return self._us / 1_000_000

    @property
    def days(self):
        return self._tuple(2)[0]

    @property
    def seconds(self):
        return self._tuple(3)[1]

    @property
    def microseconds(self):
        return self._tuple(3)[2]

    def __add__(self, other):
        if isinstance(other, datetime):
            return other.__add__(self)
        else:
            us = other._us
        return timedelta(0, 0, self._us + us)

    def __sub__(self, other):
        return timedelta(0, 0, self._us - other._us)

    def __neg__(self):
        return timedelta(0, 0, -self._us)

    def __pos__(self):
        return self

    def __abs__(self):
        return -self if self._us < 0 else self

    def __mul__(self, other):
        return timedelta(0, 0, round(other * self._us))

    __rmul__ = __mul__

    def __truediv__(self, other):
        if isinstance(other, timedelta):
            return self._us / other._us
        else:
            return timedelta(0, 0, round(self._us / other))

    def __floordiv__(self, other):
        if isinstance(other, timedelta):
            return self._us // other._us
        else:
            return timedelta(0, 0, int(self._us // other))

    def __mod__(self, other):
        return timedelta(0, 0, self._us % other._us)

    def __divmod__(self, other):
        q, r = divmod(self._us, other._us)
        return q, timedelta(0, 0, r)

    def __eq__(self, other):
        return self._us == other._us

    def __le__(self, other):
        return self._us <= other._us

    def __lt__(self, other):
        return self._us < other._us

    def __ge__(self, other):
        return self._us >= other._us

    def __gt__(self, other):
        return self._us > other._us

    def __bool__(self):
        return self._us != 0

    def __str__(self):
        return self._format(0x40)

    def __hash__(self):
        if not hasattr(self, "_hash"):
            self._hash = hash(self._us)
        return self._hash

    def isoformat(self):
        return self._format(0)

    def _format(self, spec=0):
        if self._us >= 0:
            td = self
            g = ""
        else:
            td = -self
            g = "-"
        d, h, m, s, us = td._tuple(5)
        ms, us = divmod(us, 1000)
        r = ""
        if spec & 0x40:
            spec &= ~0x40
            hr = str(h)
        else:
            hr = f"{h:02d}"
        if spec & 0x20:
            spec &= ~0x20
            spec |= 0x10
            r += "UTC"
        if spec & 0x10:
            spec &= ~0x10
            if not g:
                g = "+"
        if d:
            p = "s" if d > 1 else ""
            r += f"{g}{d} day{p}, "
            g = ""
        if spec == 0:
            spec = 5 if (ms or us) else 3
        if spec >= 1 or h:
            r += f"{g}{hr}"
            if spec >= 2 or m:
                r += f":{m:02d}"
                if spec >= 3 or s:
                    r += f":{s:02d}"
                    if spec >= 4 or ms:
                        r += f".{ms:03d}"
                        if spec >= 5 or us:
                            r += f"{us:03d}"
        return r

    def tuple(self):
        return self._tuple(5)

    def _tuple(self, n):
        d, us = divmod(self._us, 86_400_000_000)
        if n == 2:
            return d, us
        s, us = divmod(us, 1_000_000)
        if n == 3:
            return d, s, us
        h, s = divmod(s, 3600)
        m, s = divmod(s, 60)
        return d, h, m, s, us


timedelta.min = timedelta(days=-999_999_999)
timedelta.max = timedelta(days=999_999_999, hours=23, minutes=59, seconds=59, microseconds=999_999)
timedelta.resolution = timedelta(microseconds=1)
