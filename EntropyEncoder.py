from OBitstream import OBitstream


def bitsUsed(value: int) -> int:
    counter = 0

    while value != 0:
        value = int(value // 2)
        counter += 1

    return counter


class EntropyEncoder:
    def __init__(self, bitstream: OBitstream):
        self.bitstream = bitstream

    def expGolomb(self, value: int):
        assert (value >= 0)

        classIndex = bitsUsed(value + 1) - 1  # class index

        self.bitstream.addBits(1, classIndex + 1)
        self.bitstream.addBits(value + 1, classIndex)

    def writeQIndex(self, level: int):
        """ Writes a positive or negative value with exp golomb coding and sign bit
        """
        if level == 0:
            self.bitstream.addBit(0)
            return
        elif abs(level) == 1:
            self.bitstream.addBit(1)
            self.bitstream.addBit(0)
            self.bitstream.addBit(level > 0)
            return

        # sig flag: is level unequal to zero?
        self.bitstream.addBit(1)

        # gt1 flag: is absolute value greater than one?
        self.bitstream.addBit(abs(level) > 1)

        # remainder
        self.expGolomb(abs(level)-2)

        self.bitstream.addBit(level > 0)

    def writeQIndexBlock(self, qIdxBlock):
        """ Writes all values sequential to the bitstream
        """
        qIdxList = qIdxBlock.ravel()
        for k in range(qIdxList.shape[0]):
            self.writeQIndex(qIdxList[k])

    # placeholder: will make sense for arithmetic coding
    def terminate(self):
        return True
