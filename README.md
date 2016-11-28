# Adafruit's Register library
This library provides a variety of data descriptor class for Adafruit's
MicroPython that makes it really simple to write a device driver for an I2C or
SPI register based device. Data descriptors act like basic attributes from the
outside which makes using them really easy.

## Creating a driver
Creating a driver with the register library is really easy. First, import the register modules you need from the [available modules](adafruit_register/index.html):

    from adafruit_register import i2c_bit

Next, define where the bit is located in the device's memory map:

    class HelloWorldDevice:
        """Device with two bits to control when the words 'hello' and 'world' are lit."""

        hello = i2c_bit.RWBit(0x0, 0x0)
        """Bit to indicate if hello is lit."""

        world = i2c_bit.RWBit(0x1, 0x0)
        """Bit to indicate if world is lit."""

Lastly, we need to add two instance members `i2c` and `device_address` so that
the register classes know how to talk to the device. Make sure their names are
exact, otherwise the registers will not be able to find them. Also, make sure
that the i2c device implements the `nativeio.I2C` interface.

        def __init__(self, i2c, device_address=0x0):
            self.i2c = i2c
            self.device_address = device_address

Thats it! Now we have a class we can use to talk to those registers:

    import nativeio
    from board import *

    with nativeio.I2C(SCL, SDA) as i2c:
        device = HelloWorldDevice(i2c)
        device.hello = True
        device.world = True

## Adding register types
Adding a new register type is a little more complicated because you need to be careful and minimize the amount of memory the class will take. If you don't, then a driver with five registers of your type could take up five times more extra memory.

First, determine whether the new register class should go in an existing module or not. When in doubt choose a new module. The more finer grained the modules are, the fewer extra classes a driver needs to load in.

Here is the start of the `RWBit` class:

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

The first thing done is writing an RST formatted class comment that explains the
functionality of the register class and any requirements of the register layout.
It also documents the parameters passed into the constructor (`__init__`) which
configure the register location in the device map. It does not include the
device address or the i2c object because its shared on the device class instance
instead. That way if you have multiple of the same device on the same bus, the
register classes will be shared.

In `__init__` we only use two member variable because each costs 8 bytes of
memory plus the memory for the value. And remember this gets multiplied by the
number of registers of this type in a device! Thats why we pack both the
register address and data byte into one bytearray. We could use two byte arrays
of size one but each MicroPython object is 16 bytes minimum due to the garbage
collector. So, by sharing a byte array we keep it to the 16 byte minimum instead
of 32 bytes. `memoryview`s also cost 16 bytes minimum so we avoid them too.

Another thing we could do is allocate the `bytearray` only when we need it. This
has the advantage of taking less memory up front but the cost of allocating it
every access and risking it failing. If you want to add a version of `Foo` that
lazily allocates the underlying buffer call it `FooLazy`.

Ok, onward. To make a [data descriptor](https://docs.python.org/3/howto/descriptor.html)
we must implement `__get__` and `__set__`.

    def __get__(self, obj, objtype=None):
        obj.i2c.writeto(obj.device_address, self.buffer, end=1, stop=False)
        obj.i2c.readfrom_into(obj.device_address, self.buffer, start=1)
        return bool(self.buffer[1] & self.bit_mask)

    def __set__(self, obj, value):
        obj.i2c.writeto(obj.device_address, self.buffer, end=1, stop=False)
        obj.i2c.readfrom_into(obj.device_address, self.buffer, start=1)
        if value:
            self.buffer[1] |= self.bit_mask
        else:
            self.buffer[1] &= ~self.bit_mask
        obj.i2c.writeto(obj.device_address, self.buffer)

As you can see, we have two places to get state from. First, `self` stores the
register class members which locate the register within the device memory map.
Second, `obj` is the device class that uses the register class which must by
definition provide a `nativeio.I2C` compatible object as ``i2c`` and the 7-bit
device address as ``device_address``.

Note that we take heavy advantage of the ``start`` and ``end`` parameters to the
i2c functions to slice the buffer without actually allocating anything extra.
They function just like ``self.buffer[start:end]`` without the extra allocation.

Thats it! Now you can use your new register class like the example above. Just
remember to keep the number of members to a minimum because the class may be
used a bunch of times.
