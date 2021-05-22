class IBitstream:
    # constructor: open specified input file
    def __init__(self, filename):
        self.file = open(filename, 'rb')
        if not self.file:
            raise Exception('IBitstream: Could not open file')
        self.availBits = 0
        self.buffer = 0

    def get_bit(self) -> int:
        """Reads a single bit from the bitstream

            :return next bit value 0 or 1
        """
        if self.availBits == 0:
            byte_s = self.file.read(1)
            if not byte_s:
                raise Exception('IBitstream: Tried to read byte after eof')
            self.buffer = byte_s[0]
            self.availBits = 8
        self.availBits -= 1
        return (self.buffer >> self.availBits) & 1

    def get_bits(self, num_bits: int) -> int:
        """Read multiple bits from the bitstream, most significant bit first

            :param      num_bits: Specifies the numbers of bits to read
            :return:    integer representation of bits read
        """
        if num_bits <= self.availBits:
            self.availBits -= num_bits
            return (self.buffer >> self.availBits) & ((1 << num_bits) - 1)
        value = 0
        if self.availBits:
            value = self.buffer & ((1 << self.availBits) - 1)
            num_bits -= self.availBits
            self.availBits = 0
        while num_bits >= 8:
            byte_s = self.file.read(1)
            if not byte_s:
                raise Exception('IBitstream: Tried to read byte after eof')
            value = (value << 8) | int(byte_s[0])
            num_bits -= 8
        if num_bits > 0:
            byte_s = self.file.read(1)
            if not byte_s:
                raise Exception('IBitstream: Tried to read byte after eof')
            self.buffer = byte_s[0]
            self.availBits = 8 - num_bits
            value = (value << num_bits) | (self.buffer >> self.availBits)
        return value

    def byteAlign(self):
        self.availBits = 0
