# SPDX-FileCopyrightText: Copyright (c) 2022 Max Holliday
# SPDX-FileCopyrightText: Copyright (c) 2026 Tim Cocks for Adafruit Industries
#
# SPDX-License-Identifier: MIT
"""
`adafruit_register.paged_i2c_register_accessor`
====================================================

Paged I2C Register Accessor class.

* Author(s): Tim Cocks
* Adapted from work by Max Holliday
"""

from adafruit_register.register_accessor import I2CRegisterAccessor

try:
    from typing import Union

    from adafruit_bus_device.i2c_device import I2CDevice
except ImportError:
    pass

__version__ = "0.0.0+auto.0"
__repo__ = "https://github.com/adafruit/Adafruit_CircuitPython_Register.git"


class PagedI2CRegisterAccessor(I2CRegisterAccessor):
    """
    RegisterAccessor class for I2C devices whose register space is split into
    pages. Devices using this scheme reach a register in two steps: a page number is
    written to a fixed register, and every access after that is an offset
    within the page that was selected.

    Register addresses given to the descriptors are the two-byte form the
    datasheets print, ``page << 8 | register``: address ``0x2001`` is register
    ``0x01`` of page ``0x20``. That keeps a driver's register constants
    readable against its datasheet while ordinary ``RWBit``, ``RWBits``,
    ``UnaryStruct`` and ``Struct`` descriptors do the work.

    The selected page is remembered, so a run of accesses to one page costs a
    single transaction each; only a change of page adds a second one. Nothing
    else on the bus may write this device's page register behind the
    accessor's back. To recover from that state, call `forget_page`, after any reset
    that returns the device to its power-on page.

    :param I2CDevice i2c_device: I2C device to communicate over
    :param int page_select_register: The register the page number is written
      to. Nearly always ``0x00``, which is the default.
    :param int autoincrement_bit: A bit in the register address byte that asks
      the device to walk through consecutive registers during a multi-byte
      transfer. It is set for reads and writes longer than one byte, and the
      register address is masked to the bits below it. Leave it ``0`` for
      devices that autoincrement unconditionally or not at all.
    """

    def __init__(
        self,
        i2c_device: I2CDevice,
        page_select_register: int = 0x00,
        autoincrement_bit: int = 0x00,
    ):
        super().__init__(i2c_device, address_width=1, lsb_first=False)
        self.page_select_register = page_select_register
        self.autoincrement_bit = autoincrement_bit
        self._register_mask = 0xFF & ~autoincrement_bit
        self._page = None
        self._page_buffer = bytearray(2)

    def forget_page(self) -> None:
        """
        Forget which page is selected, so that the next access selects one
        again. Use after a device reset, or if something else has written
        the device's page register.

        :return: None
        """
        self._page = None

    def select_page(self, address: int, length: int = 1) -> int:
        """
        Select the page ``address`` lives on, if it is not already selected,
        and return the address byte to use within it.

        :param int address: The two-byte page and register address.
        :param int length: The number of data bytes about to be transferred,
          which decides whether the autoincrement bit is set.
        :return: The register address byte, autoincrement bit included.
        """
        page = address >> 8
        if page != self._page:
            self._page_buffer[0] = self.page_select_register
            self._page_buffer[1] = page
            with self.i2c_device as i2c:
                i2c.write(self._page_buffer)
            self._page = page
        register = address & self._register_mask
        if length > 1:
            register |= self.autoincrement_bit
        return register

    def read_register(self, address: int, buffer: bytearray):
        """
        Read register value over I2CDevice, selecting its page first.

        :param int address: The two-byte page and register address to read.
        :param bytearray buffer: Buffer that will be used to read register data into.
        :return: None
        """
        super().read_register(self.select_page(address, len(buffer)), buffer)

    def write_register(self, address: int, buffer: bytearray):
        """
        Write register value over I2CDevice, selecting its page first.

        :param int address: The two-byte page and register address to write.
        :param bytearray buffer: Buffer of data that will be written to the register.
        :return: None
        """
        super().write_register(self.select_page(address, len(buffer)), buffer)
