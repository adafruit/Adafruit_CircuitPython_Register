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
    """
    Subclasses of this class will be used to provide read/write interface to registers
    over different bus types.

    :param int address_width: The width of the register addresses in bytes. Defaults to 1.
    :param bool lsb_first: Is the first byte we read from the bus the LSB? Defaults to true
    """

    address_width = None

    def __init__(self, address_width=1, lsb_first=True):
        self.address_width = address_width
        self.address_buffer = bytearray(address_width)
        self.lsb_first = lsb_first

    def _pack_address_into_buffer(self, address):
        if self.lsb_first:
            # Little-endian: least significant byte first
            for address_byte_i in range(self.address_width):
                self.address_buffer[address_byte_i] = (address >> (address_byte_i * 8)) & 0xFF
        else:
            # Big-endian: most significant byte first
            big_endian_address = address.to_bytes(self.address_width, byteorder="big")
            for address_byte_i in range(self.address_width):
                self.address_buffer[address_byte_i] = big_endian_address[address_byte_i]


class SPIRegisterAccessor(RegisterAccessor):
    """
    RegisterAccessor class for SPI bus transport. Provides interface to read/write
    registers over SPI. This class automatically handles the R/W bit by setting the
    highest bit of the address to 1 when reading and 0 when writing. For multi-byte
    addresses the R/W bit will be set as the highest bit in the first byte of the
    address.

    :param SPIDevice spi_device: The SPI bus device to communicate over.
    :param int address_width: The number of bytes in the address
    """

    def __init__(self, spi_device: SPIDevice, address_width: int = 1, lsb_first=True):
        super().__init__(address_width, lsb_first)
        self.spi_device = spi_device

    def _shift_rw_cmd_bit_into_first_byte(self, bit_value):
        if bit_value not in {0, 1}:
            raise ValueError("bit_value must be 0 or 1")

        # Clear the MSB (set bit 7 to 0)
        cleared_byte = self.address_buffer[0] & 0x7F
        # Set the MSB to the desired bit value
        self.address_buffer[0] = cleared_byte | (bit_value << 7)

    def read_register(self, address: int, buffer: bytearray):
        """
        Read register value over SPIDevice.

        :param int address: The register address to read.
        :param bytearray buffer: Buffer that will be used to read register data into.
        :return: None
        """

        self._pack_address_into_buffer(address)
        self._shift_rw_cmd_bit_into_first_byte(1)
        with self.spi_device as spi:
            spi.write(self.address_buffer)
            spi.readinto(buffer)

    def write_register(
        self,
        address: int,
        buffer: bytearray,
    ):
        """
        Write register value over SPIDevice.

        :param int address: The register address to read.
        :param bytearray buffer: Buffer that will be written to the register.
        :return: None
        """
        self._pack_address_into_buffer(address)
        self._shift_rw_cmd_bit_into_first_byte(0)
        with self.spi_device as spi:
            spi.write(self.address_buffer)
            spi.write(buffer)


class I2CRegisterAccessor(RegisterAccessor):
    """
    RegisterAccessor class for I2C bus transport. Provides interface to read/write
    registers over I2C. This class uses `adafruit_bus_device.I2CDevice` for
    communication. I2CDevice automatically handles the R/W bit by setting
    the lowest bit of the device address to 1 for reading and 0 for writing.
    Device address & r/w bit will be written first, followed by register address,
    then the data will be written or read.

    :param I2CDevice i2c_device: I2C device to communicate over
    :param int address_width: The number of bytes in the address
    """

    def __init__(self, i2c_device: I2CDevice, address_width: int = 1, lsb_first=True):
        super().__init__(address_width, lsb_first)
        self.i2c_device = i2c_device

        # buffer that will hold address + data for write operations, will grow as needed
        self._full_buffer = bytearray(address_width + 1)

    def read_register(self, address: int, buffer: bytearray):
        """
        Read register value over I2CDevice.

        :param int address: The register address to read.
        :param bytearray buffer: Buffer that will be used to read register data into.
        :return: None
        """

        self._pack_address_into_buffer(address)
        with self.i2c_device as i2c:
            i2c.write_then_readinto(self.address_buffer, buffer)

    def write_register(self, address: int, buffer: bytearray):
        """
        Write register value over I2CDevice.

        :param int address: The register address to read.
        :param bytearray buffer: Buffer of data that will be written to the register.
        :return: None
        """
        # grow full buffer if needed
        if self.address_width + len(buffer) > len(self._full_buffer):
            self._full_buffer = bytearray(self.address_width + len(buffer))

        # put address into full buffer
        self._pack_address_into_buffer(address)
        self._full_buffer[: self.address_width] = self.address_buffer

        # put data into full buffer
        self._full_buffer[self.address_width : self.address_width + len(buffer)] = buffer

        with self.i2c_device as i2c:
            i2c.write(self._full_buffer, end=self.address_width + len(buffer))
