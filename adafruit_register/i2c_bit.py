class RWBit:
    def __init__(self, register_address, bit):
        self.bit_mask = 1 << bit
        self.buffer = bytearray(2)
        self.buffer[0] = register_address

    def __get__(self, obj, objtype=None):
        obj.i2c.writeto(obj.device_address, self.buffer, length=1, stop=False)
        obj.i2c.readfrom_into(obj.device_address, self.buffer, offset=1)
        return bool(self.buffer[1] & mask)

    def __set__(self, obj, value):
        obj.i2c.writeto(obj.device_address, self.buffer, length=1, stop=False)
        obj.i2c.readfrom_into(obj.device_address, self.buffer, offset=1)
        if value:
            self.buffer[1] |= self.bit_mask
        else:
            self.buffer[1] &= ~self.bit_mask
        obj.i2c.writeto(obj.device_address, self.buffer)

class ROBit(RWBit):
    def __set__(self, obj, value):
        raise AttributeError()
