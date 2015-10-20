import math

import bitstring

class ReverseBitReader(object):
    def __init__(self, stream):
        self.stream = stream
        self.latest_chunk = bitstring.BitArray('')

    def read(self, size, reverse=False):
        missing_bits = max(0, size - self.latest_chunk.length)
        missing_bytes = int(math.ceil(missing_bits / 8.0))

        for x in range(missing_bytes):
            next_byte = bitstring.BitArray(self.stream.read(8))
            next_byte.reverse()
            self.latest_chunk.append(next_byte)

        chunk = self.latest_chunk[0:size]
        del self.latest_chunk[0:size]

        if reverse:
            chunk.reverse()

        return chunk

