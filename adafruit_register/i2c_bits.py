# The MIT License (MIT)
#
# Copyright (c) 2016 Scott Shawcroft for Adafruit Industries
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

class RWBits:
    """
    Multibit register (less than a full byte) that is readable and writeable.
    This must be within a byte register.

    Values are `int` between 0 and 2 ** ``num_bits`` - 1.

    :param int num_bits: The number of bits in the field.
    :param int register_address: The register address to read the bit from
    :param type lowest_bit: The lowest bits index within the byte at ``register_address``
    """
    def __init__(self, num_bits, register_address, lowest_bit):
        self.bit_mask = 0
        for i in range(num_bits):
            self.bit_mask = (self.bit_mask << 1) + 1
        self.bit_mask = self.bit_mask << lowest_bit
        if self.bit_mask >= (1 << 8):
            raise ValueError()
        self.buffer = bytearray(2)
        self.buffer[0] = register_address
        self.lowest_bit = lowest_bit

    def __get__(self, obj, objtype=None):
        with obj.i2c_device as i2c:
            i2c.write(self.buffer, end=1, stop=False)
            i2c.readinto(self.buffer, start=1)
        return (self.buffer[1] & self.bit_mask) >> self.lowest_bit

    def __set__(self, obj, value):
        # Shift the value to the appropriate spot and set all bits that aren't
        # ours to 1 (the negation of the bitmask.)
        value = (value << self.lowest_bit) | ~self.bit_mask
        with obj.i2c_device as i2c:
            i2c.write(self.buffer, end=1, stop=False)
            i2c.readinto(self.buffer, start=1)
            # Set all of our bits to 1.
            self.buffer[1] |= self.bit_mask
            # Set all 0 bits to 0 by anding together.
            self.buffer[1] &= value
            i2c.write(self.buffer)

class ROBits(RWBits):
    """
    Multibit register (less than a full byte) that is read-only. This must be
    within a byte register.

    Values are `int` between 0 and 2 ** ``num_bits`` - 1.

    :param int num_bits: The number of bits in the field.
    :param int register_address: The register address to read the bit from
    :param type lowest_bit: The lowest bits index within the byte at ``register_address``
    """
    def __set__(self, obj, value):
        raise AttributeError()
