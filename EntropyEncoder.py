import numpy as np

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
        self.prob_gt1_flag = ProbModel()
        self.prob_level_prefix = ProbModel()
        self.prob_cbf = ProbModel()
        self.prob_last_prefix = ProbModel()
        self.est_bits = 0

    # NOTE: no longer required, replaced expGolombProbAdapted
    def expGolomb(self, value: int):
        assert (value >= 0)

        classIndex = bitsUsed(value + 1) - 1  # class index

        self.arith_enc.encodeBinsEP(1, classIndex + 1)
        self.arith_enc.encodeBinsEP(value + 1, classIndex)

    def expGolombProbAdapted(self, value: int, prob, estimation=False):
        assert (value >= 0)

        classIndex = bitsUsed(value + 1) - 1  # class index

        if not estimation:
            self.arith_enc.encodeBins(1, classIndex + 1, prob)
            self.arith_enc.encodeBinsEP(value + 1, classIndex)
        else:
            while classIndex > 0:
                classIndex -= 1
                self.est_bits += self.arith_enc.getEstBits((1 >> classIndex + 1) & 1, prob)
            self.est_bits += 1

    def writeQIndex(self, level: int, isLast=False):
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
            self.arith_enc.encodeBin(0, self.prob_gt1_flag)
            self.arith_enc.encodeBinEP(level > 0)
            return

        # sig flag: is level unequal to zero?
        if not isLast:
            self.arith_enc.encodeBin(1, self.prob_sig_flag)

        # gt1 flag: is absolute value greater than one?
        self.arith_enc.encodeBin(abs(level) > 1, self.prob_gt1_flag)

        # remainder
        self.expGolombProbAdapted(abs(level) - 2, self.prob_level_prefix)

        self.arith_enc.encodeBinEP(level > 0)

    def getEstimateBits(self, level, isLast=False):
        if level == 0:
            if isLast:
                raise ValueError('Should not occur')
            self.est_bits += self.arith_enc.getEstBits(0, self.prob_sig_flag)
            return
        elif abs(level) == 1:
            if not isLast:
                self.est_bits += self.arith_enc.getEstBits(1, self.prob_sig_flag)
            self.est_bits += self.arith_enc.getEstBits(0, self.prob_gt1_flag)
            self.est_bits += 1
            return
            # sig flag: is level unequal to zero?
        if not isLast:
            self.est_bits += self.arith_enc.getEstBits(1, self.prob_sig_flag)

        # gt1 flag: is absolute value greater than one?
        self.est_bits += self.arith_enc.getEstBits(abs(level) > 1, self.prob_gt1_flag)

        # remainder
        self.expGolombProbAdapted(abs(level) - 2, self.prob_level_prefix, estimation=True)

        self.est_bits += 1

    def writeQIndexBlock(self, qIdxBlock):
        """ Writes all values sequential to the bitstream
        """
        qIdxList = qIdxBlock.ravel()

        coded_block_flag = np.any(qIdxList != 0)
        self.arith_enc.encodeBin(coded_block_flag, self.prob_cbf)
        if not coded_block_flag:
            return

        last_scan_index = np.max(np.nonzero(qIdxList))
        # last_scan_index = (np.where(qIdxList != 0))[-1]  # that doesn't work (returns a list)
        self.expGolombProbAdapted(last_scan_index, self.prob_last_prefix)

        self.writeQIndex(qIdxList[last_scan_index], isLast=True)
        # self.getEstimateBits(qIdxList[last_scan_index], isLast=True)
        for k in range(last_scan_index - 1, -1, -1):
            self.writeQIndex(qIdxList[k])

    # placeholder: will make sense for arithmetic coding
    def terminate(self):
        self.arith_enc.finalize()
        return True

    def estBits(self, predMode, qIdxBlock):
        qIdxList = qIdxBlock.ravel()

        coded_block_flag = np.any(qIdxList != 0)
        self.est_bits += self.arith_enc.getEstBits(coded_block_flag, self.prob_cbf)
        if not coded_block_flag:
            return 0

        last_scan_index = np.max(np.nonzero(qIdxList))
        self.expGolombProbAdapted(last_scan_index, self.prob_last_prefix, estimation=True)

        self.getEstimateBits(qIdxList[last_scan_index], isLast=True)
        for k in range(last_scan_index - 1, -1, -1):
            self.getEstimateBits(qIdxList[k])

        return self.est_bits
