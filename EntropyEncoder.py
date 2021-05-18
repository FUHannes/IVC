from OBitstream import OBitstream
from arithBase import ProbModel
from arithEncoder import ArithEncoder

def bitsUsed(value: int) -> int:
    counter = 0

    while value != 0:
        value = int(value // 2)
        counter += 1

    return counter


class EntropyEncoder:
    def __init__(self, bitstream: OBitstream):
        self.arith_enc = ArithEncoder(bitstream)
        self.prob_sig_flag = ProbModel()

    def expGolomb(self, value: int):
        assert (value >= 0)

        classIndex = bitsUsed(value + 1) - 1  # class index

        self.arith_enc.encodeBinsEP(1, classIndex + 1)
        self.arith_enc.encodeBinsEP(value + 1, classIndex)

    def writeQIndex(self, level: int):
        """ Writes a positive or negative value with exp golomb coding and sign bit
        """
        if level == 0:
            self.arith_enc.encodeBin(0, self.prob_sig_flag)
            return
        elif abs(level) == 1:
            self.arith_enc.encodeBin(1, self.prob_sig_flag)
            self.arith_enc.encodeBinEP(0)
            self.arith_enc.encodeBinEP(level > 0)
            return

        # sig flag: is level unequal to zero?
        self.arith_enc.encodeBin(1, self.prob_sig_flag)

        # gt1 flag: is absolute value greater than one?
        self.arith_enc.encodeBinEP(abs(level) > 1)

        # remainder
        self.expGolomb(abs(level)-2)

        self.arith_enc.encodeBinEP(level > 0)

    def writeQIndexBlock(self, qIdxBlock):
        """ Writes all values sequential to the bitstream
        """
        qIdxList = qIdxBlock.ravel()
        for k in range(qIdxList.shape[0]):
            self.writeQIndex(qIdxList[k])

    # placeholder: will make sense for arithmetic coding
    def terminate(self):
        self.arith_enc.finalize()
        return True
