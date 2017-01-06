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

import time

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

    The byte order of the register must* be: second, minute, hour, weekday, day (1-31), month, year (in years after 2000).

    \* Setting weekday_first=False will flip the weekday/day order so that day comes first.

    Values are `DateTimeTuple`

    :param int register_address: The register address to start the read
    :param bool weekday_first: True if weekday is in a lower register than the day of the month (1-31)
    :param int weekday_start: 0 or 1 depending on the RTC's representation of the first day of the week
    """
    def __init__(self, register_address, weekday_first=True, weekday_start=1):
        self.buffer = bytearray(8)
        self.buffer[0] = register_address
        if weekday_first:
            self.weekday_offset = 0
        else:
            self.weekday_offset = 1
        self.weekday_start = weekday_start

    def __get__(self, obj, objtype=None):
        # Read and return the date and time.
        with obj.i2c_device:
            obj.i2c_device.writeto(self.buffer, end=1, stop=False)
            obj.i2c_device.readfrom_into(self.buffer, start=1)
        return datetime_tuple(
            year=_bcd2bin(self.buffer[7]) + 2000,
            month=_bcd2bin(self.buffer[6]),
            day=_bcd2bin(self.buffer[5 - self.weekday_offset]),
            weekday=_bcd2bin(self.buffer[4 + self.weekday_offset] - self.weekday_start),
            hour=_bcd2bin(self.buffer[3]),
            minute=_bcd2bin(self.buffer[2]),
            second=_bcd2bin(self.buffer[1] & 0x7F),
        )

    def __set__(self, obj, value):
        self.buffer[1] = _bin2bcd(value.second) & 0x7F   # format conversions
        self.buffer[2] = _bin2bcd(value.minute)
        self.buffer[3] = _bin2bcd(value.hour)
        self.buffer[4 + self.weekday_offset] = _bin2bcd(value.weekday + self.weekday_start)
        self.buffer[5 - self.weekday_offset] = _bin2bcd(value.day)
        self.buffer[6] = _bin2bcd(value.month)
        self.buffer[7] = _bin2bcd(value.year - 2000)
        with obj.i2c_device:
            obj.i2c_device.writeto(self.buffer)

ALARM_COMPONENT_DISABLED = 0x80

FREQUENCY = ["secondly", "minutely", "hourly", "daily", "weekly", "monthly"]

class BCDAlarmTimeRegister:
    """
    Alarm date and time register using binary coded decimal structure.

    The byte order of the registers must* be: [second], minute, hour, day,
    weekday. Each byte must also have a high enable bit where 1 is disabled and
    0 is enabled.

    * If weekday_shared is True, then weekday and day share a register.
    * If has_seconds is True, then there is a seconds register.

    Values are a tuple of (`time.struct_time`, `str`) where the struct represents
    a date and time that would alarm. The string is the frequency:

    * "secondly", once a second (only if alarm has_seconds)
    * "minutely", once a minute when seconds match (if alarm doesn't seconds then when seconds = 0)
    * "hourly", once an hour when `tm_min` and `tm_sec` match
    * "daily", once a day when `tm_hour`, `tm_min` and `tm_sec` match
    * "weekly", once a week when `tm_wday`, `tm_hour`, `tm_min`, `tm_sec` match
    * "monthly", once a month when `tm_mday`, `tm_hour`, `tm_min`, `tm_sec` match

    :param int register_address: The register address to start the read
    :param bool has_seconds: True if the alarm can happen minutely.
    :param bool weekday_shared: True if weekday and day share the same register
    :param int weekday_start: 0 or 1 depending on the RTC's representation of the first day of the week (Monday)
    """
    # Defaults are based on alarm1 of the DS3231.
    def __init__(self, register_address, has_seconds=True, weekday_shared=True, weekday_start=1):
        buffer_size = 5
        if weekday_shared:
            buffer_size -= 1
        if has_seconds:
            buffer_size += 1
        self.has_seconds = has_seconds
        self.buffer = bytearray(buffer_size)
        self.buffer[0] = register_address
        self.weekday_shared = weekday_shared
        self.weekday_start = weekday_start

    def __get__(self, obj, objtype=None):
        # Read the alarm register.
        with obj.i2c_device:
            obj.i2c_device.writeto(self.buffer, end=1, stop=False)
            obj.i2c_device.readfrom_into(self.buffer, start=1)
        frequency = None

        while (self.buffer[i] & 0x80) != 0:
            return None
        return datetime_tuple(
            weekday=_bcd2bin(self.buffer[3] & 0x7f) - self.weekday_start,
            day=_bcd2bin(self.buffer[4] & 0x7f),
            hour=_bcd2bin(self.buffer[2] & 0x7f),
            minute=_bcd2bin(self.buffer[1] & 0x7f),
        )

    def __set__(self, obj, value):
        minute = ALARM_COMPONENT_DISABLED
        if value.minute is not None:
            minute = _bin2bcd(value.minute)
        self.buffer[1] = minute

        hour = ALARM_COMPONENT_DISABLED
        if value.hour is not None:
            hour = _bin2bcd(value.hour)
        self.buffer[2] = hour

        if not self.weekday_shared:
            day = ALARM_COMPONENT_DISABLED
            self.buffer[4] = (_bin2bcd(value.day) if value.day is not None else 0x80)

        self.buffer[3 + self.weekday_offset] = (_bin2bcd(value.weekday + self.weekday_start) | 0b01000000 if value.weekday is not None else 0x80)

        with obj.i2c_device:
            obj.i2c_device.writeto(self.buffer)
