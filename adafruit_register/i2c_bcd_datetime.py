# SPDX-FileCopyrightText: 2016 Scott Shawcroft for Adafruit Industries
#
# SPDX-License-Identifier: MIT
# pylint: disable=too-few-public-methods

"""
`adafruit_register.i2c_bcd_datetime`
====================================================

Binary Coded Decimal date and time register

* Author(s): Scott Shawcroft
"""

__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_Register.git"

import time

try:
    from typing import Optional, Type
    from typing_extensions import Literal
    from circuitpython_typing.device_drivers import I2CDeviceDriver
except ImportError:
    pass


def _bcd2bin(value: int) -> int:
    """Convert binary coded decimal to Binary

    :param value: the BCD value to convert to binary (required, no default)
    """
    return value - 6 * (value >> 4)


def _bin2bcd(value: int) -> int:
    """Convert a binary value to binary coded decimal.

    :param value: the binary value to convert to BCD. (required, no default)
    """
    return value + 6 * (value // 10)


class BCDDateTimeRegister:
    """
    Date and time register using binary coded decimal structure.

    The byte order of the register must* be: second, minute, hour, weekday, day (1-31), month, year
    (in years after 2000).

    * Setting weekday_first=False will flip the weekday/day order so that day comes first.

    Values are `time.struct_time`

    :param int register_address: The register address to start the read
    :param bool weekday_first: True if weekday is in a lower register than the day of the month
        (1-31)
    :param int weekday_start: 0 or 1 depending on the RTC's representation of the first day of the
        week
    """

    def __init__(
        self,
        register_address: int,
        weekday_first: bool = True,
        weekday_start: Literal[0, 1] = 1,
    ) -> None:
        self.buffer = bytearray(8)
        self.buffer[0] = register_address
        if weekday_first:
            self.weekday_offset = 0
        else:
            self.weekday_offset = 1
        self.weekday_start = weekday_start
        # Masking value list   n/a  sec min hr day wkday mon year
        self.mask_datetime = b"\xFF\x7F\x7F\x3F\x3F\x07\x1F\xFF"

    def __get__(
        self,
        obj: Optional[I2CDeviceDriver],
        objtype: Optional[Type[I2CDeviceDriver]] = None,
    ) -> time.struct_time:
        # Read and return the date and time.
        with obj.i2c_device as i2c:
            i2c.write_then_readinto(self.buffer, self.buffer, out_end=1, in_start=1)
        return time.struct_time(
            (
                _bcd2bin(self.buffer[7] & self.mask_datetime[7]) + 2000,
                _bcd2bin(self.buffer[6] & self.mask_datetime[6]),
                _bcd2bin(self.buffer[5 - self.weekday_offset] & self.mask_datetime[4]),
                _bcd2bin(self.buffer[3] & self.mask_datetime[3]),
                _bcd2bin(self.buffer[2] & self.mask_datetime[2]),
                _bcd2bin(self.buffer[1] & self.mask_datetime[1]),
                _bcd2bin(
                    (self.buffer[4 + self.weekday_offset] & self.mask_datetime[5])
                    - self.weekday_start
                ),
                -1,
                -1,
            )
        )

    def __set__(self, obj: I2CDeviceDriver, value: time.struct_time) -> None:
        self.buffer[1] = _bin2bcd(value.tm_sec) & 0x7F  # format conversions
        self.buffer[2] = _bin2bcd(value.tm_min)
        self.buffer[3] = _bin2bcd(value.tm_hour)
        self.buffer[4 + self.weekday_offset] = _bin2bcd(
            value.tm_wday + self.weekday_start
        )
        self.buffer[5 - self.weekday_offset] = _bin2bcd(value.tm_mday)
        self.buffer[6] = _bin2bcd(value.tm_mon)
        self.buffer[7] = _bin2bcd(value.tm_year - 2000)
        with obj.i2c_device:
            obj.i2c_device.write(self.buffer)
