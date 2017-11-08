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

class RWBit:
    """
    Single bit register that is readable and writeable.

    Values are `bool`

    :param int register_address: The register address to read the bit from
    :param type bit: The bit index within the byte at ``register_address``
    """
    def __init__(self, register_address, bit):
        self.bit_mask = 1 << bit
        self.buffer = bytearray(2)
        self.buffer[0] = register_address

    def __get__(self, obj, objtype=None):
        with obj.i2c_device as i2c:
            i2c.write(self.buffer, end=1, stop=False)
            i2c.readinto(self.buffer, start=1)
        return bool(self.buffer[1] & self.bit_mask)

    def __set__(self, obj, value):
        with obj.i2c_device as i2c:
            i2c.write(self.buffer, end=1, stop=False)
            i2c.readinto(self.buffer, start=1)
            if value:
                self.buffer[1] |= self.bit_mask
            else:
                self.buffer[1] &= ~self.bit_mask
            i2c.write(self.buffer)

class ROBit(RWBit):
    """Single bit register that is read only. Subclass of `RWBit`.

    Values are `bool`

    :param int register_address: The register address to read the bit from
    :param type bit: The bit index within the byte at ``register_address``"""
    def __set__(self, obj, value):
        raise AttributeError()
