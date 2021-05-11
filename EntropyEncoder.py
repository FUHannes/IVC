
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

        # bitsUsed is 'real' bits used - 1
        self.expGolomb(abs(level))

        if level > 0:
            self.bitstream.addBit(0)
        elif level < 0:
            self.bitstream.addBit(1)

    def writeQIndexBlock(self, qIdxBlock):
        """ Writes all values sequential to the bitstream
        """
        qIdxList = qIdxBlock.ravel()
        for k in range( qIdxList.shape[0] ):
            self.writeQIndex(qIdxList[k])

