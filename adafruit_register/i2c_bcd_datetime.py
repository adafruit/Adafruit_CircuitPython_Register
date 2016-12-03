# The MIT License (MIT)
#
# Copyright (c) 2016 Scott Shawcroft for Adafruit Industries
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

try:
    import ucollections as collections
except:
    import collections

# TODO(tannewt): Split out the datetime tuple stuff so it can be shared more widely.
DateTimeTuple = collections.namedtuple("DateTimeTuple", ["year", "month",
    "day", "weekday", "hour", "minute", "second", "millisecond"])

def datetime_tuple(year, month, day, weekday=0, hour=0, minute=0,
                    second=0, millisecond=0):
    """Converts individual values into a `DateTimeTuple` with defaults.

    :param int year: The year
    :param int month: The month
    :param int day: The day
    :param int weekday: The day of the week (0-6)
    :param int hour: The hour
    :param int minute: The minute
    :param int second: The second
    :param int millisecond: not supported
    :return: The date and time
    :rtype: DateTimeTuple
    """
    return DateTimeTuple(year, month, day, weekday, hour, minute,second,
        millisecond)

def _bcd2bin(value):
    """Convert binary coded decimal to Binary

    Arguments:
    value - the BCD value to convert to binary (required, no default)
    """
    return value - 6 * (value >> 4)


def _bin2bcd(value):
    """Convert a binary value to binary coded decimal.

    Arguments:
    value - the binary value to convert to BCD. (required, no default)
    """
    return value + 6 * (value // 10)

class BCDDateTimeRegister:
    """
    Date and time register using binary coded decimal structure.

    The byte order of the register must be: second, minute, hour, weekday, day, month, year (in years after 2000).

    Values are `DateTimeTuple`

    :param int register_address: The register address to start the read
    """
    def __init__(self, register_address):
        self.buffer = bytearray(8)
        self.buffer[0] = register_address

    def __get__(self, obj, objtype=None):
        # Read and return the date and time.
        with obj.i2c_device:
            obj.i2c_device.writeto(self.buffer, end=1, stop=False)
            obj.i2c_device.readfrom_into(self.buffer, start=1)
        return datetime_tuple(
            year=_bcd2bin(self.buffer[7]) + 2000,
            month=_bcd2bin(self.buffer[6]),
            day=_bcd2bin(self.buffer[5]),
            weekday=_bcd2bin(self.buffer[4]),
            hour=_bcd2bin(self.buffer[3]),
            minute=_bcd2bin(self.buffer[2]),
            second=_bcd2bin(self.buffer[1]),
        )

    def __set__(self, obj, value):
        self.buffer[1] = _bin2bcd(value.second)   # format conversions
        self.buffer[2] = _bin2bcd(value.minute)
        self.buffer[3] = _bin2bcd(value.hour)
        self.buffer[4] = _bin2bcd(value.weekday)
        self.buffer[5] = _bin2bcd(value.day)
        self.buffer[6] = _bin2bcd(value.month)
        self.buffer[7] = _bin2bcd(value.year - 2000)
        with obj.i2c_device:
            obj.i2c_device.writeto(self.buffer)

class BCDAlarmTimeRegister:
    """
    Date and time register using binary coded decimal structure.

    The byte order of the register must be: minute, hour, day, weekday.

    Values are `DateTimeTuple` with year, month and seconds ignored.

    :param int register_address: The register address to start the read
    """
    def __init__(self, register_address):
        self.buffer = bytearray(5)
        self.buffer[0] = register_address

    def __get__(self, obj, objtype=None):
        # Read the alarm register.
        with obj.i2c_device:
            obj.i2c_device.writeto(self.buffer, end=1, stop=False)
            obj.i2c_device.readfrom_into(self.buffer, start=1)
        if not self.buffer[1] & 0x80:
            return None
        return datetime_tuple(
            weekday=_bcd2bin(self.buffer[4] & 0x7f),
            day=_bcd2bin(self.buffer[3] & 0x7f),
            hour=_bcd2bin(self.buffer[2] & 0x7f),
            minute=_bcd2bin(self.buffer[1] & 0x7f),
        )

    def __set__(self, obj, value):
        self.buffer[1] = (_bin2bcd(value.minute) if value.minute is not None else 0x80)
        self.buffer[2] = (_bin2bcd(value.hour) if value.hour is not None else 0x80)
        self.buffer[3] = (_bin2bcd(value.day) if value.day is not None else 0x80)
        self.buffer[4] = (_bin2bcd(value.weekday) | 0b01000000 if value.weekday is not None else 0x80)
        with obj.i2c_device:
            obj.i2c_device.writeto(self.buffer)
