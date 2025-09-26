# SPDX-FileCopyrightText: Copyright (c) 2025 Tim Cocks for Adafruit Industries
#
# SPDX-License-Identifier: MIT
"""
`adafruit_register.register_bit`
====================================================

Single bit registers that use RegisterAccessor

* Author(s): Tim Cocks

"""

__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_Register.git"


class RWBit:
    """
    Single bit register that is readable and writeable.

    Values are `bool`

    :param int register_address: The register address to read the bit from
    :param int bit: The bit index within the byte at ``register_address``
    :param int register_width: The number of bytes in the register. Defaults to 1.
    :param bool lsb_first: Is the first byte we read from spi the LSB? Defaults to true

    """

    def __init__(
        self,
        register_address: int,
        bit: int,
        register_width: int = 1,
        lsb_first: bool = True,
        address_width: int = 1,
    ):
        self.bit_mask = 1 << (bit % 8)  # the bitmask *within* the byte!

        self.address = register_address

        self.address_width = address_width
        self.buffer = bytearray(address_width + register_width)

        # Pack possible multibyte address into the buffer
        for i in range(address_width):
            if lsb_first:
                # Little-endian: least significant byte first
                self.buffer[i] = (register_address >> (i * 8)) & 0xFF
            else:
                # Big-endian: most significant byte first
                self.buffer[i] = (register_address >> ((address_width - 1 - i) * 8)) & 0xFF

        self.lsb_first = lsb_first
        self.bit_index = bit
        if lsb_first:
            self.byte = address_width + (bit // 8)  # Little-endian: bit 0 in first register byte
        else:
            self.byte = (
                address_width + register_width - 1 - (bit // 8)
            )  # Big-endian: bit 0 in last register byte

    def __get__(self, obj, objtype=None):
        # read data from register
        obj.register_accessor.read_register(self.buffer)

        # check specified bit and return boolean
        return bool(self.buffer[self.byte] & self.bit_mask)

    def __set__(self, obj, value):
        # read current data from register
        obj.register_accessor.read_register(self.buffer)

        # update current data with new value
        if value:
            self.buffer[self.byte] |= self.bit_mask
        else:
            self.buffer[self.byte] &= ~self.bit_mask

        # write updated data to register
        obj.register_accessor.write_register(self.buffer)


class ROBit(RWBit):
    """Single bit register that is read only. Subclass of `RWBit`.

    Values are `bool`

    :param int register_address: The register address to read the bit from
    :param type bit: The bit index within the byte at ``register_address``
    :param int register_width: The number of bytes in the register. Defaults to 1.

    """

    def __set__(self, obj, value):
        raise AttributeError()
