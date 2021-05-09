from bitarray import bitarray


class IBitstream:
    def __init__(self, filename=None):
        self.filename = filename
        self._bitarray = None
        self.read_file()

    def read_file(self):
        if self.filename:
            with open(self.filename, 'rb') as fp:
                self._bitarray = bitarray()
                self._bitarray.fromfile(fp)

    def get_bit(self) -> int:
        """Reads a single bit from the bitstream

            :return next bit value 0 or 1
        """
        return self._bitarray.pop(0)

    def get_bits(self, num_bits: int) -> int:
        """Read multiple bits from the bitstream, most significant bit first

            :param      num_bits: Specifies the numbers of bits to read
            :return:    integer representation of bits read
            :raises     IndexError: if bitarray is empty or index is out of range
        """
        _int = int(self._bitarray[:num_bits].to01(), 2)
        self._bitarray = self._bitarray[num_bits:]
        return _int

    def num_available_bits(self) -> int:
        """

        :return: number of still available bits in the bitstream
        """
        return len(self._bitarray)

    @property
    def bitarray(self):
        return self._bitarray


if __name__ == '__main__':
    i_bit_stream = IBitstream()
    num_array = [166, 184]
    _bit_array = bitarray()

    for n in num_array:
        _bit_array.frombytes(n.to_bytes(1, 'little'))

    i_bit_stream._bitarray = _bit_array

    print(i_bit_stream.get_bit(),   i_bit_stream.bitarray.to01())  # returns 1 010011010111000
    print(i_bit_stream.get_bits(5), i_bit_stream.bitarray.to01())  # returns 9 1010111000
    print(i_bit_stream.get_bits(3), i_bit_stream.bitarray.to01())  # returns 5 0111000
    print(i_bit_stream.get_bits(6), i_bit_stream.bitarray.to01())  # returns 28 0
