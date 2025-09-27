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


class RegisterAccessor:
    address_width = None

    def _pack_address_into_buffer(self, address, lsb_first, buffer):
        # Pack address into the buffer
        for i in range(self.address_width):
            if lsb_first:
                # Little-endian: least significant byte first
                buffer[i] = (address >> (i * 8)) & 0xFF
            else:
                # Big-endian: most significant byte first
                big_endian_address = address.to_bytes(self.address_width, byteorder="big")
                for address_byte_i in range(self.address_width):
                    buffer[address_byte_i] = big_endian_address[address_byte_i]


class SPIRegisterAccessor(RegisterAccessor):
    """
    RegisterAccessor class for SPI bus transport. Provides interface to read/write
    registers over SPI.

    :param SPIDevice spi_device: The SPI bus device to communicate over.
    :param int address_width: The number of bytes in the address
    """

    def __init__(self, spi_device: SPIDevice, address_width: int = 1):
        self.address_width = address_width
        self.spi_device = spi_device

    def _shift_rw_cmd_bit_into_address_byte(self, buffer, bit_value):
        if bit_value not in {0, 1}:
            raise ValueError("bit_value must be 0 or 1")

        # Clear the MSB (set bit 7 to 0)
        cleared_byte = buffer[0] & 0x7F
        # Set the MSB to the desired bit value
        buffer[0] = cleared_byte | (bit_value << 7)

    def read_register(self, address: int, lsb_first: bool, buffer: bytearray):
        """
        Read register value over SPIDevice.

        :param int address: The register address to read.
        :param bool lsb_first: Is the first byte we read from the bus the LSB?
        :param bytearray buffer: Buffer that will be used to write/read register data.
          `address` will be put into the first `address_width` bytes of the buffer, data
          will be read into the buffer following the address.
          Buffer must be long enough to be read all data sent by the device.
        :return: None
        """

        self._pack_address_into_buffer(address, lsb_first, buffer)
        self._shift_rw_cmd_bit_into_address_byte(buffer, 1)
        with self.spi_device as spi:
            spi.write(buffer, end=1)
            spi.readinto(buffer, start=1)

    def write_register(
        self,
        address: int,
        lsb_first: bool,
        buffer: bytearray,
    ):
        """
        Write register value over SPIDevice.

        :param int address: The register address to read.
        :param bool lsb_first: Is the first byte we read from the bus the LSB?
        :param bytearray buffer: Buffer that will be written to the register.
          `address` will be put into the first `address_width` bytes of the buffer
        :return: None
        """
        self._pack_address_into_buffer(address, lsb_first, buffer)
        self._shift_rw_cmd_bit_into_address_byte(buffer, 0)
        with self.spi_device as spi:
            self._shift_rw_cmd_bit_into_address_byte(buffer, 0)
            spi.write(buffer)


class I2CRegisterAccessor(RegisterAccessor):
    """
    RegisterAccessor class for I2C bus transport. Provides interface to read/write
    registers over I2C

    :param I2CDevice i2c_device: I2C device to communicate over
    :param int address_width: The number of bytes in the address
    """

    def __init__(self, i2c_device: I2CDevice, address_width: int = 1):
        self.i2c_device = i2c_device
        self.address_width = address_width

    def read_register(self, address: int, lsb_first: bool, buffer: bytearray):
        """
        Read register value over I2CDevice.

        :param int address: The register address to read.
        :param bool lsb_first: Is the first byte we read from the bus the LSB? Defaults to true
        :param bytearray buffer: Buffer that will be used to write/read register data.
          address will be put into the first `address_width` bytes of the buffer, data
          will be read into the buffer following the address.
          Buffer must be long enough to be read all data sent by the device.
        :return: None
        """

        self._pack_address_into_buffer(address, lsb_first, buffer)
        with self.i2c_device as i2c:
            i2c.write_then_readinto(
                buffer, buffer, out_end=self.address_width, in_start=self.address_width
            )

    def write_register(self, address: int, lsb_first: bool, buffer: bytearray):
        """
        Write register value over I2CDevice.

        :param int address: The register address to read.
        :param bool lsb_first: Is the first byte we read from the bus the LSB? Defaults to true
        :param bytearray buffer: Buffer must have register address value at index 0.
          Must be long enough to be read all data send by the device for specified register.

        :return: None
        """
        self._pack_address_into_buffer(address, lsb_first, buffer)
        with self.i2c_device as i2c:
            i2c.write(buffer)
