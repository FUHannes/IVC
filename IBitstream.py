
class IBitstream:
    # constructor: open specified input file (and read all data)
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
        return ( self.buffer >> self.availBits ) & 1

    def get_bits(self, num_bits: int) -> int:
        """Read multiple bits from the bitstream, most significant bit first

            :param      num_bits: Specifies the numbers of bits to read
            :return:    integer representation of bits read
            :raises     IndexError: if bitarray is empty or index is out of range
        """
        value = 0
        for _ in range(num_bits):
            value = value << 1
            value += self.get_bit()
        return value

    def byteAlign(self):
        while (self.availBits != 0):
            self.get_bit()

