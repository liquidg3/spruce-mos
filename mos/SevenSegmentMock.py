class SevenSegmentMock:
    def __init__(self, address=0x70, i2c=None, **kwargs):
        self.address = address
        print('instantiating %s' % self.address)

    def set_colon(self, enabled):
        pass
        # print("colon %s to %s" % (self.address, enabled))

    def print_float(self, value, decimal_digits=2, justify_right=True):
        print("setting %s to %s" % (self.address, value))

    def begin(self):
        print("beginning on LED %s" % self.address)

    def write_display(self):
        # print("writing display to %s" % self.address)
        pass

    def clear(self):
        # print('clearing %s' % self.address)
        pass