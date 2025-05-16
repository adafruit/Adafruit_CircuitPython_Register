# SPDX-FileCopyrightText: 2016 Scott Shawcroft for Adafruit Industries
#
# SPDX-License-Identifier: MIT

"""
`adafruit_register.i2c_bit`
====================================================

Single bit registers

* Author(s): Scott Shawcroft
"""

__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_Register.git"

try:
    from typing import NoReturn, Optional, Type

    from circuitpython_typing.device_drivers import I2CDeviceDriver
except ImportError:
    pass


class RWBit:
    """
    Single bit register that is readable and writeable.

    Values are `bool`

    :param int register_address: The register address to read the bit from
    :param int bit: The bit index within the byte at ``register_address``
    :param int register_width: The number of bytes in the register. Defaults to 1.
    :param bool lsb_first: Is the first byte we read from I2C the LSB? Defaults to true

    """

    def __init__(
        self,
        register_address: int,
        bit: int,
        register_width: int = 1,
        lsb_first: bool = True,
    ) -> None:
        self.bit_mask = 1 << (bit % 8)  # the bitmask *within* the byte!
        self.buffer = bytearray(1 + register_width)
        self.buffer[0] = register_address
        if lsb_first:
            self.byte = bit // 8 + 1  # the byte number within the buffer
        else:
            self.byte = register_width - (bit // 8)  # the byte number within the buffer

    def __get__(
        self,
        obj: Optional[I2CDeviceDriver],
        objtype: Optional[Type[I2CDeviceDriver]] = None,
    ) -> bool:
        with obj.i2c_device as i2c:
            i2c.write_then_readinto(self.buffer, self.buffer, out_end=1, in_start=1)
        return bool(self.buffer[self.byte] & self.bit_mask)

    def __set__(self, obj: I2CDeviceDriver, value: bool) -> None:
        with obj.i2c_device as i2c:
            i2c.write_then_readinto(self.buffer, self.buffer, out_end=1, in_start=1)
            if value:
                self.buffer[self.byte] |= self.bit_mask
            else:
                self.buffer[self.byte] &= ~self.bit_mask
            i2c.write(self.buffer)


class ROBit(RWBit):
    """Single bit register that is read only. Subclass of `RWBit`.

    Values are `bool`

    :param int register_address: The register address to read the bit from
    :param type bit: The bit index within the byte at ``register_address``
    :param int register_width: The number of bytes in the register. Defaults to 1.

    """

    def __set__(self, obj: I2CDeviceDriver, value: bool) -> NoReturn:
        raise AttributeError()
