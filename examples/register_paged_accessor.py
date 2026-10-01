# SPDX-FileCopyrightText: 2026 Tim Cocks for Adafruit Industries
# SPDX-License-Identifier: MIT
"""
Read a paged register space with PagedI2CRegisterAccessor.

Some I2C devices do not carry a register address wide enough for their whole
register map. Instead, they split it into pages: a page number is written to a
fixed register, and every access after that is an offset within that page.

Descriptors address such a device with the two-byte form its datasheet prints,
``page << 8 | register``. Here ``0x1001`` is register ``0x01`` of page
``0x10``, and reading two bytes from it walks into ``0x1002`` as well, because
the CS42L42 asks for autoincrementing with the top bit of the register address
byte. A device that autoincrements unconditionally, or not at all, leaves
``autoincrement_bit`` at its default of 0.

Requires a Cirrus Logic CS42L42 codec, held out of reset, on the I2C bus.
"""

import board
from adafruit_bus_device.i2c_device import I2CDevice

from adafruit_register.register_accessor import PagedI2CRegisterAccessor
from adafruit_register.register_bits import ROBits
from adafruit_register.register_struct import ROUnaryStruct

I2C_ADDRESS = 0x48
REG_DEVID_AB = 0x1001  # page 0x10, register 0x01
REG_REVID = 0x1005  # page 0x10, register 0x05


class CS42L42Tester:
    # Two consecutive one-byte registers, read in a single transaction.
    chip_id = ROUnaryStruct(REG_DEVID_AB, ">H")
    # The revision register splits into two nibbles.
    metal_revision = ROBits(4, REG_REVID, 0)
    analog_revision = ROBits(4, REG_REVID, 4)

    def __init__(self, i2c):
        self.register_accessor = PagedI2CRegisterAccessor(
            I2CDevice(i2c, I2C_ADDRESS), autoincrement_bit=0x80
        )


if __name__ == "__main__":
    codec = CS42L42Tester(board.I2C())
    print(f"chip id: 0x{codec.chip_id:04X}")
    print(f"revision: analog {codec.analog_revision}, metal {codec.metal_revision}")
