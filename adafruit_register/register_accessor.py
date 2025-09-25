# SPDX-FileCopyrightText: Copyright (c) 2022 Max Holliday
# SPDX-FileCopyrightText: Copyright (c) 2025 Tim Cocks for Adafruit Industries
#
# SPDX-License-Identifier: MIT
"""
`adafruit_register.register_accessor`
====================================================

SPI and I2C Register Accessor classes.

* Author(s): Max Holliday
* Adaptation by Tim Cocks
"""

__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_Register.git"


class SPIRegisterAccessor:
    def __init__(self, spi_device):
        self.spi_device = spi_device

    def _shift_rw_cmd_bit_into_address_byte(self, buffer, bit_value):
        if bit_value not in {0, 1}:
            raise ValueError("bit_value must be 0 or 1")

        # Clear the MSB (set bit 7 to 0)
        cleared_byte = buffer[0] & 0x7F
        # Set the MSB to the desired bit value
        buffer[0] = cleared_byte | (bit_value << 7)

    def read_register(self, buffer):
        with self.spi_device as spi:
            self._shift_rw_cmd_bit_into_address_byte(buffer, 1)
            spi.write(buffer, end=1)
            spi.readinto(buffer, start=1)

    def write_register(self, buffer, value, lsb_first, bit_mask, lowest_bit, byte=None):
        # read current register data
        with self.spi_device as spi:
            self._shift_rw_cmd_bit_into_address_byte(buffer, 1)
            spi.write(buffer, end=1)
            spi.readinto(buffer, start=1)

        if isinstance(value, int):
            # shift in integer value to register data
            reg = 0
            order = range(len(buffer) - 1, 0, -1)
            if not lsb_first:
                order = range(1, len(buffer))
            for i in order:
                reg = (reg << 8) | buffer[i]

            shifted_value = value << lowest_bit
            reg &= ~bit_mask  # mask off the bits we're about to change
            reg |= shifted_value  # then or in our new value

            # put data from reg back into buffer
            for i in reversed(order):
                buffer[i] = reg & 0xFF
                reg >>= 8
        elif isinstance(value, bool):
            # shift in single bit value to register data
            if value:
                buffer[byte] |= bit_mask
            else:
                buffer[byte] &= ~bit_mask

        # write updated register data
        with self.spi_device as spi:
            self._shift_rw_cmd_bit_into_address_byte(buffer, 0)
            spi.write(buffer)


class I2CRegisterAccessor:
    def __init__(self, i2c_device):
        self.i2c_device = i2c_device
        pass

    def read_register(self, buffer):
        with self.i2c_device as i2c:
            i2c.write_then_readinto(buffer, buffer, out_end=1, in_start=1)

    def write_register(self, buffer, value, lsb_first, bit_mask, lowest_bit, byte=None):

        value <<= lowest_bit  # shift the value over to the right spot
        with self.i2c_device as i2c:
            i2c.write_then_readinto(buffer, buffer, out_end=1, in_start=1)

            reg = 0
            order = range(len(buffer) - 1, 0, -1)
            if not lsb_first:
                order = range(1, len(buffer))
            for i in order:
                reg = (reg << 8) | buffer[i]
            # print("old reg: ", hex(reg))
            reg &= ~bit_mask  # mask off the bits we're about to change
            reg |= value  # then or in our new value
            # print("new reg: ", hex(reg))
            for i in reversed(order):
                buffer[i] = reg & 0xFF
                reg >>= 8
            i2c.write(buffer)
