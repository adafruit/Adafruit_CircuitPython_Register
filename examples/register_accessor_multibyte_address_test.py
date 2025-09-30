# SPDX-FileCopyrightText: 2025 Tim Cocks for Adafruit Industries
# SPDX-License-Identifier: MIT
"""
Verify functionality of multibyte address registers.

Rrequires OV5640 camera connected.
Default pins are for RPi Pico + Adafruit PiCowbell Camera Breakout
"""

import board
import busio
import digitalio
from adafruit_bus_device.i2c_device import I2CDevice

from adafruit_register.register_accessor import I2CRegisterAccessor
from adafruit_register.register_bits import ROBits

I2C_ADDRESS = 0x3C
REG_CHIP_ID_HIGH = 0x300A


class OV5640Tester:
    chip_id = ROBits(16, REG_CHIP_ID_HIGH, 0, register_width=2, lsb_first=False)

    def __init__(self, i2c):
        try:
            i2c_device = I2CDevice(i2c, I2C_ADDRESS)
            self.register_accessor = I2CRegisterAccessor(
                i2c_device, address_width=2, lsb_first=False
            )
        except ValueError:
            raise ValueError(f"No I2C device found.")


if __name__ == "__main__":
    print("construct bus")
    i2c = busio.I2C(board.GP5, board.GP4)
    print("construct camera")
    reset = digitalio.DigitalInOut(board.GP14)

    ov5640 = OV5640Tester(i2c)
    print(hex(ov5640.chip_id))
