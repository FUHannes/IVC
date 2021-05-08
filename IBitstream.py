class IBitstream:
    def __init__(self, filename):
        self.filename = filename
        pass

    def get_bit(self) -> int:
        """Reads a single bit from the bitstream

            :return next bit value 0 or 1
        """
        pass

    def get_bits(self, num_bits: int) -> int:
        """Read multiple bits from the bitstream, most significant bit first

            :param      num_bits: Specifies the numbers of bits to read
            :return:    integer representation of bits read
            :raises     ValueException: In case num_bit is less than zero
        """
        if num_bits < 0:
            raise ValueError('num_bits must be a non negative value')
        pass

    def num_available_bits(self) -> int:
        """

        :return: number of still available bits in the bitstream
        """
        pass
