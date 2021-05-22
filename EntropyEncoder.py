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
        self.prob_cbf = ProbModel()
        self.prob_golomb_suffix = ProbModel()

    def expGolomb(self, value: int):
        assert (value >= 0)

        classIndex = bitsUsed(value + 1) - 1  # class index

        self.arith_enc.encodeBinsEP(1, classIndex + 1)
        self.arith_enc.encodeBinsEP(value + 1, classIndex)

    def expGolombProbAdapted(self, value: int):
        assert (value >= 0)

        classIndex = bitsUsed(value + 1) - 1  # class index

        self.arith_enc.encodeBins(1, classIndex + 1, self.prob_golomb_suffix)
        self.arith_enc.encodeBinsEP(value + 1, classIndex)

    def writeQIndex(self, level: int):
        """ Writes a positive or negative value with exp golomb coding and sign bit
        """
        if level == 0:
            if isLast:
                raise ValueError('Should not occur')
            self.arith_enc.encodeBin(0, self.prob_sig_flag)
            return
        elif abs(level) == 1:
            if not isLast:
                self.arith_enc.encodeBin(1, self.prob_sig_flag)
            self.arith_enc.encodeBinEP(0)
            self.arith_enc.encodeBinEP(level > 0)
            return

        # sig flag: is level unequal to zero?
        if not isLast:
            self.arith_enc.encodeBin(1, self.prob_sig_flag)

        # gt1 flag: is absolute value greater than one?
        self.arith_enc.encodeBinEP(abs(level) > 1)

        # remainder
        self.expGolomb(abs(level) - 2)

        self.arith_enc.encodeBinEP(level > 0)

    def writeQIndexBlock(self, qIdxBlock):
        """ Writes all values sequential to the bitstream
        """
        qIdxList = qIdxBlock.ravel()

        coded_block_flag = np.any(qIdxList != 0)
        self.self.arith_enc.encodeBin(coded_block_flag, self.prob_cbf)
        if not coded_block_flag:
            return

        last_scan_index = np.where(qIdxList != 0)[-1]
        self.expGolombProbAdapted(last_scan_index)

        self.writeQIndex(qIdxList[last_scan_index], isLast=True)
        for k in range(last_scan_index-1, -1, -1):
            self.writeQIndex(qIdxList[k])

    # placeholder: will make sense for arithmetic coding
    def terminate(self):
        self.arith_enc.finalize()
        return True
