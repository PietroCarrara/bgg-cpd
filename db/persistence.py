import struct

class Uint32PairPersist:
    def __init__(self):
        # Two uint32
        self.data_size = 4 * 2
        self.pattern = 'II'

    def to_bytes(self, obj):
        if obj == None:
            return bytes([0] * self.data_size)

        a, b = obj
        return struct.pack(self.pattern, a, b)

    def from_bytes(self, arr):
        assert len(arr) == self.data_size

        pair = struct.unpack(self.pattern, arr)

        if pair == (0, 0):
            return None

        return pair