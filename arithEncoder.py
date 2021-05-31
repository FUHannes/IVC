from arithBase import LPSTable
from arithBase import RenormTable


# ----- arithmetic encoder  -----
class ArithEncoder:

    # constructor:
    #    - bitstream = OBitstream  object
    #    - initialize  class  members  
    def __init__(self, bitstream):
        self.bitstream = bitstream
        self.bitstream.byteAlign()
        self.low: int = 0
        self.range: int = 510
        self.bufferedByte: int = 255
        self.numBufferedBytes: int = 0
        self.bitsLeft: int = 23

    # adaptive coding:
    #  - encodes binary decision (bin) using specified probability model
    #  - updates probability model based on value of bin
    def encodeBin(self, bin: int, probModel):
        LPS: int = LPSTable[probModel.state()][(self.range >> 6) & 3]
        self.range -= LPS
        if bin != probModel.mps():
            numBits: int = RenormTable[LPS >> 3]
            self.low = (self.low + self.range) << numBits
            self.range = LPS << numBits
            self.bitsLeft -= numBits
            self.__test_and_write_out()
            probModel.updateLPS()
        else:
            if self.range < 256:
                self.low <<= 1
                self.range <<= 1
                self.bitsLeft -= 1
                self.__test_and_write_out()
            probModel.updateMPS()

    # wrapper for encodeBin() to handle multiple bins
    def encodeBins(self, pattern: int, numBins: int, probModel):
        while numBins > 0:
            numBins -= 1
            self.encodeBin((pattern >> numBins) & 1, probModel)

    # bypass coding of a single bin
    def encodeBinEP(self, bin: int):
        self.low <<= 1
        if bin:
            self.low += self.range
        self.bitsLeft -= 1
        self.__test_and_write_out()

    # bypass coding of multiple bins
    def encodeBinsEP(self, pattern: int, numBins: int):
        while numBins > 8:
            numBins -= 8
            patternPart = (pattern >> numBins) & 255
            self.low = (self.low << 8) + int(self.range * patternPart)
            self.bitsLeft -= 8
            self.__test_and_write_out()
        patternPart = pattern & ((1 << numBins) - 1)
        self.low = (self.low << numBins) + int(self.range * patternPart)
        self.bitsLeft -= numBins
        self.__test_and_write_out()

    # finalization of arithmetic codeword (required at end)
    def finalize(self):
        # terminating bin
        self.range -= 2
        self.low += self.range
        self.low <<= 7
        self.range = 2 << 7
        self.bitsLeft -= 7
        self.__test_and_write_out()
        # finish codeword
        if (self.low >> (32 - self.bitsLeft)) > 0:
            self.bitstream.addBits(self.bufferedByte + 1, 8)
            while self.numBufferedBytes > 1:
                self.bitstream.addBits(0, 8)
                self.numBufferedBytes -= 1
            self.low -= (1 << (32 - self.bitsLeft))
        else:
            if self.numBufferedBytes > 0:
                self.bitstream.addBits(self.bufferedByte, 8)
            while self.numBufferedBytes > 1:
                self.bitstream.addBits(255, 8)
                self.numBufferedBytes -= 1
        self.bitstream.addBits(self.low >> 8, 24 - self.bitsLeft)
        self.bitstream.addBit(1)
        self.bitstream.byteAlign()

    # private method for output
    def __test_and_write_out(self):
        if self.bitsLeft < 12:
            leadByte: int = self.low >> (24 - self.bitsLeft)
            self.bitsLeft += 8
            self.low &= (4294967295 >> self.bitsLeft)
            if leadByte == 255:
                self.numBufferedBytes += 1
            else:
                if self.numBufferedBytes > 0:
                    carry: int = leadByte >> 8
                    byte: int = self.bufferedByte + carry
                    self.bufferedByte = leadByte & 255
                    self.bitstream.addBits(byte, 8)
                    byte = (255 + carry) & 255
                    while self.numBufferedBytes > 1:
                        self.bitstream.addBits(byte, 8)
                        self.numBufferedBytes -= 1
                else:
                    self.numBufferedBytes = 1
                    self.bufferedByte = leadByte
