# SPDX-FileCopyrightText: Copyright (c) 2025 Tim Cocks for Adafruit Industries
#
# SPDX-License-Identifier: MIT
"""
`adafruit_register.register_bits`
====================================================

Multi bit registers

* Author(s): Tim Cocks

"""

import time


class RWBits:
    """
    Multibit register (less than a full byte) that is readable and writeable.
    This must be within a byte register.

    Values are `int` between 0 and 2 ** ``num_bits`` - 1.

    :param int num_bits: The number of bits in the field.
    :param int register_address: The register address to read the bit from
    :param int lowest_bit: The lowest bits index within the byte at ``register_address``
    :param int register_width: The number of bytes in the register. Defaults to 1.
    :param bool lsb_first: Is the first byte we read from SPI the LSB? Defaults to true
    """

    # pylint: disable=too-many-arguments
    def __init__(
        self,
        num_bits,
        register_address,
        lowest_bit,
        register_width=1,
        lsb_first=True,
    ):
        self.bit_mask = ((1 << num_bits) - 1) << lowest_bit

        if self.bit_mask >= 1 << (register_width * 8):
            raise ValueError("Cannot have more bits than register size")
        self.lowest_bit = lowest_bit
        self.buffer = bytearray(1 + register_width)
        self.buffer[0] = register_address
        self.buffer[1] = register_width - 1
        self.lsb_first = lsb_first

    def __get__(self, obj, objtype=None):
        obj.register_accessor.read_register(self.buffer)

        # read the bytes into a single variable
        reg = 0
        order = range(len(self.buffer) - 1, 0, -1)
        if not self.lsb_first:
            order = reversed(order)
        for i in order:
            reg = (reg << 8) | self.buffer[i]

        # extract integer value from specified bits
        result = (reg & self.bit_mask) >> self.lowest_bit
        return result

    def __set__(self, obj, value):
        obj.register_accessor.write_register(
            self.buffer, value, self.lsb_first, self.bit_mask, self.lowest_bit
        )


class ROBits(RWBits):
    """
    Multibit register (less than a full byte) that is read-only. This must be
    within a byte register.

    Values are `int` between 0 and 2 ** ``num_bits`` - 1.

    :param int num_bits: The number of bits in the field.
    :param int register_address: The register address to read the bit from
    :param type lowest_bit: The lowest bits index within the byte at ``register_address``
    :param int register_width: The number of bytes in the register. Defaults to 1.
    """

    def __set__(self, obj, value):
        raise AttributeError()
