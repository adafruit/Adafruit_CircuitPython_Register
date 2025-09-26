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


try:
    from typing import Union

    from adafruit_bus_device.i2c_device import I2CDevice
    from adafruit_bus_device.spi_device import SPIDevice
except ImportError:
    pass


class SPIRegisterAccessor:
    """
    RegisterAccessor class for SPI bus transport. Provides interface to read/write
    registers over SPI.

    :param SPIDevice spi_device: The SPI bus device to communicate over.
    """

    def __init__(self, spi_device: SPIDevice):
        self.spi_device = spi_device

    def _shift_rw_cmd_bit_into_address_byte(self, buffer, bit_value):
        if bit_value not in {0, 1}:
            raise ValueError("bit_value must be 0 or 1")

        # Clear the MSB (set bit 7 to 0)
        cleared_byte = buffer[0] & 0x7F
        # Set the MSB to the desired bit value
        buffer[0] = cleared_byte | (bit_value << 7)

    def read_register(self, buffer: bytearray):
        """
        Read register value over SPIDevice.

        :param bytearray buffer: Buffer must have register address value at index 0.
          Must be long enough to be read all data send by the device. Data will be
          read into indexes 1-N.
        :return: None
        """
        with self.spi_device as spi:
            self._shift_rw_cmd_bit_into_address_byte(buffer, 1)
            spi.write(buffer, end=1)
            spi.readinto(buffer, start=1)

    def write_register(
        self,
        buffer: bytearray,
    ):
        """
        Write register value over SPIDevice.

        :param bytearray buffer: Buffer must have register address value at index 0.
          Must be long enough to be read all data send by the device for specified register.
        :return: None
        """

        with self.spi_device as spi:
            self._shift_rw_cmd_bit_into_address_byte(buffer, 0)
            spi.write(buffer)


class I2CRegisterAccessor:
    """
    RegisterAccessor class for I2C bus transport. Provides interface to read/write
    registers over I2C

    :param I2CDevice i2c_device: I2C device to communicate over
    """

    def __init__(self, i2c_device: I2CDevice):
        self.i2c_device = i2c_device
        pass

    def read_register(self, buffer):
        """
        Read register value over I2CDevice.

        :param bytearray buffer: Buffer must have register address value at index 0.
          Must be long enough to be read all data send by the device. Data will be
          read into indexes 1-N.
        :return: None
        """
        with self.i2c_device as i2c:
            i2c.write_then_readinto(buffer, buffer, out_end=1, in_start=1)

    def write_register(self, buffer):
        """
        Write register value over I2CDevice.

        :param bytearray buffer: Buffer must have register address value at index 0.
          Must be long enough to be read all data send by the device for specified register.
        :return: None
        """

        with self.i2c_device as i2c:
            i2c.write(buffer)
