# SPDX-FileCopyrightText: Copyright (c) 2025 Tim Cocks for Adafruit Industries
#
# SPDX-License-Identifier: MIT
"""
`adafruit_register.register_bits`
====================================================

Multi bit registers

* Author(s): Tim Cocks

"""

__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_Register.git"


class RWBits:
    """
    Multibit register that is readable and writeable.

    Values are `int` between 0 and 2 ** ``num_bits`` - 1.

    :param int num_bits: The number of bits in the field.
    :param int register_address: The register address to read the bit from
    :param int lowest_bit: The lowest bits index within the byte at ``register_address``
    :param int register_width: The number of bytes in the register. Defaults to 1.
    :param bool lsb_first: Is the first byte we read from the bus the LSB? Defaults to true
    :param bool signed: If True, the value is a "two's complement" signed value.
      If False, it is unsigned.

    """

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        num_bits: int,
        register_address: int,
        lowest_bit: int,
        register_width: int = 1,
        lsb_first: bool = True,
        signed: bool = False,
    ):
        self.bit_mask = ((1 << num_bits) - 1) << lowest_bit

        if self.bit_mask >= 1 << (register_width * 8):
            raise ValueError("Cannot have more bits than register size")
        self.lowest_bit = lowest_bit

        self.address = register_address
        self.buffer = bytearray(register_width)

        self.lsb_first = lsb_first
        self.sign_bit = (1 << (num_bits - 1)) if signed else 0

    def __get__(self, obj, objtype=None):
        # read data from register
        obj.register_accessor.read_register(self.address, self.buffer)

        # read the bytes into a single variable
        reg = 0
        order = range(len(self.buffer) - 1, -1, -1)
        if not self.lsb_first:
            order = reversed(order)
        for i in order:
            reg = (reg << 8) | self.buffer[i]

        # extract integer value from specified bits
        result = (reg & self.bit_mask) >> self.lowest_bit

        # If the value is signed and negative, convert it
        if result & self.sign_bit:
            result -= 2 * self.sign_bit

        return result

    def __set__(self, obj, value):
        # read current data from register
        obj.register_accessor.read_register(self.address, self.buffer)

        # shift in integer value to register data
        reg = 0
        order = range(len(self.buffer) - 1, -1, -1)
        if not self.lsb_first:
            order = reversed(order)
        for i in order:
            reg = (reg << 8) | self.buffer[i]
        shifted_value = value << self.lowest_bit
        reg &= ~self.bit_mask  # mask off the bits we're about to change
        reg |= shifted_value  # then or in our new value

        # put data from reg back into buffer
        for i in reversed(order):
            self.buffer[i] = reg & 0xFF
            reg >>= 8

        # write updated data buffer to the register
        obj.register_accessor.write_register(self.address, self.buffer)


class ROBits(RWBits):
    """
    Multibit register that is read-only.

    Values are `int` between 0 and 2 ** ``num_bits`` - 1.

    :param int num_bits: The number of bits in the field.
    :param int register_address: The register address to read the bit from
    :param int lowest_bit: The lowest bits index within the byte at ``register_address``
    :param int register_width: The number of bytes in the register. Defaults to 1.
    :param bool lsb_first: Is the first byte we read from the bus the LSB? Defaults to true
    :param bool signed: If True, the value is a "two's complement" signed value.
      If False, it is unsigned.
    """

    def __set__(self, obj, value):
        raise AttributeError()
