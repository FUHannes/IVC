import numpy as np
import copy
import random

from IntraPredictionCalculator import PredictionMode
from OBitstream import OBitstream
from arithBase import ProbModel
from arithEncoder import ArithEncoder
from ContextModeler import ContextModeler


def bitsUsed(value: int) -> int:
    counter = 0

    while value != 0:
        value = int(value // 2)
        counter += 1

    return counter


class EntropyEncoder:
    def __init__(self, bitstream: OBitstream, block_size: int):
        self.arith_enc = ArithEncoder(bitstream)
        self.cm = ContextModeler(block_size)
        self.est_bits = 0
        self.block_size = block_size

    def expGolombProbAdapted(self, value: int, prob, estimation=False):
        assert (value >= 0)

        classIndex = bitsUsed(value + 1) - 1  # class index

        if not estimation:
            self.arith_enc.encodeBins(1, classIndex + 1, prob)
            self.arith_enc.encodeBinsEP(value + 1, classIndex)
        else:
            self.est_bits += classIndex # suffix part (bypass coded)
            while classIndex > 0:
                classIndex -= 1
                self.est_bits += prob.estBits(0)
            self.est_bits += prob.estBits(1)

    def writeQIndex(self, level: int, pos: int, isLast=False):
        """ Writes a positive or negative value with exp golomb coding and sign bit
        """
        self.cm.switchContext(pos)

        # TODO of exercise 8.3
        inter_flag = 1

        if inter_flag == 1:
            # choose random motion vector
            max_motion = self.block_size
            mx = random.randint(-max_motion, max_motion)
            my = random.randint(-max_motion, max_motion)

            mx_abs_greater0_flag = abs(mx) > 0
            my_abs_greater0_flag = abs(my) > 0

            mx_sign = mx > 0
            my_sign = my > 0

            self.arith_enc.encodeBin(mx_abs_greater0_flag, self.cm.prob_mx_abs_greater0_flag)
            if mx_abs_greater0_flag:
                self.expGolombProbAdapted(abs(mx), self.cm.prob_mx)
                self.arith_enc.encodeBinEP(mx_sign)

            self.arith_enc.encodeBin(my_abs_greater0_flag, self.cm.prob_my_abs_greater0_flag)
            if my_abs_greater0_flag:
                self.expGolombProbAdapted(abs(my), self.cm.prob_my)
                self.arith_enc.encodeBinEP(my_sign)

        if level == 0:
            if isLast:
                raise ValueError('Should not occur')
            self.arith_enc.encodeBin(0, self.cm.prob_sig_flag)
            return
        elif abs(level) == 1:
            if not isLast:
                self.arith_enc.encodeBin(1, self.cm.prob_sig_flag)
            self.arith_enc.encodeBin(0, self.cm.prob_gt1_flag)
            self.arith_enc.encodeBinEP(level > 0)
            return

        # sig flag: is level unequal to zero?
        if not isLast:
            self.arith_enc.encodeBin(1, self.cm.prob_sig_flag)

        # gt1 flag: is absolute value greater than one?
        self.arith_enc.encodeBin(1, self.cm.prob_gt1_flag)

        # remainder
        self.expGolombProbAdapted(abs(level) - 2, self.cm.prob_level_prefix)

        self.arith_enc.encodeBinEP(level > 0)

    # similar to writeQindex but estimation only
    def getEstimateBits(self, level, pos, isLast=False):
        self.cm.switchContext(pos)

        if level == 0:
            if isLast:
                raise ValueError('Should not occur')
            self.est_bits += self.cm.prob_sig_flag.estBits(0)
            return
        elif abs(level) == 1:
            if not isLast:
                self.est_bits += self.cm.prob_sig_flag.estBits(1)
            self.est_bits += self.cm.prob_gt1_flag.estBits(0)
            self.est_bits += 1
            return
            # sig flag: is level unequal to zero?
        if not isLast:
            self.est_bits += self.cm.prob_sig_flag.estBits(1)

        # gt1 flag: is absolute value greater than one?
        self.est_bits += self.cm.prob_gt1_flag.estBits(1)

        # remainder
        self.expGolombProbAdapted(abs(level) - 2, self.cm.prob_level_prefix, estimation=True)

        self.est_bits += 1

    def write_qindexes_block(self, qIdxBlock):
        """ Writes all quantization indexes
        """
        qIdxList = qIdxBlock.ravel()

        coded_block_flag = np.any(qIdxList != 0)
        self.arith_enc.encodeBin(coded_block_flag, self.cm.prob_cbf)
        if not coded_block_flag:
            return

        last_scan_index = np.max(np.nonzero(qIdxList))
        self.expGolombProbAdapted(last_scan_index, self.cm.prob_last_prefix)

        self.writeQIndex(qIdxList[last_scan_index], last_scan_index, isLast=True)
        for k in range(last_scan_index - 1, -1, -1):
            self.writeQIndex(qIdxList[k], k)

    def write_block_intra_pic(self, qIdxBlock, prediction_mode):
        """ Writes all values sequential to the bitstream
        """
        # write side information
        if prediction_mode == PredictionMode.PLANAR_PREDICTION:
            self.arith_enc.encodeBin(0, self.cm.prediction_mode_bin1)
        elif prediction_mode == PredictionMode.DC_PREDICTION:
            self.arith_enc.encodeBin(1, self.cm.prediction_mode_bin1)
            self.arith_enc.encodeBin(0, self.cm.prediction_mode_bin2)
        elif prediction_mode == PredictionMode.HORIZONTAL_PREDICTION:
            self.arith_enc.encodeBin(1, self.cm.prediction_mode_bin1)
            self.arith_enc.encodeBin(1, self.cm.prediction_mode_bin2)
            self.arith_enc.encodeBin(0, self.cm.prediction_mode_bin3)
        elif prediction_mode == PredictionMode.VERTICAL_PREDICTION:
            self.arith_enc.encodeBin(1, self.cm.prediction_mode_bin1)
            self.arith_enc.encodeBin(1, self.cm.prediction_mode_bin2)
            self.arith_enc.encodeBin(1, self.cm.prediction_mode_bin3)

        # write quantization indexes
        self.write_qindexes_block(qIdxBlock)

    def write_block_inter_pic(self, qIdxBlock, mx: int, my: int):
        """ Writes all values sequential to the bitstream
        """
        # write side information: later

        # write quantization indexes
        self.write_qindexes_block(qIdxBlock)

    # placeholder: will make sense for arithmetic coding
    def terminate(self):
        self.arith_enc.finalize()
        return True

    # add bits for quantization indexes (both intra and inter pictures)
    def add_bits_qindex_block(self, qIdxBlock):
        qIdxList = qIdxBlock.ravel()
        coded_block_flag = np.any(qIdxList != 0)
        self.est_bits += self.cm.prob_cbf.estBits(coded_block_flag)
        if not coded_block_flag:
            return

        last_scan_index = np.max(np.nonzero(qIdxList))
        self.expGolombProbAdapted(last_scan_index, self.cm.prob_last_prefix, estimation=True)

        self.getEstimateBits(qIdxList[last_scan_index], last_scan_index, isLast=True)
        for k in range(last_scan_index - 1, -1, -1):
            self.getEstimateBits(qIdxList[k], k)

    # similar to write_block_intra_pic but estimation only
    def est_block_bits_intra_pic(self, predMode, qIdxBlock):
        self.est_bits = 0
        org_probs = copy.deepcopy(self.cm)

        if predMode == PredictionMode.PLANAR_PREDICTION:
            self.est_bits += self.cm.prediction_mode_bin1.estBits(0)
        elif predMode == PredictionMode.DC_PREDICTION:
            self.est_bits += self.cm.prediction_mode_bin1.estBits(1)
            self.est_bits += self.cm.prediction_mode_bin2.estBits(0)
        elif predMode == PredictionMode.HORIZONTAL_PREDICTION:
            self.est_bits += self.cm.prediction_mode_bin1.estBits(1)
            self.est_bits += self.cm.prediction_mode_bin2.estBits(1)
            self.est_bits += self.cm.prediction_mode_bin3.estBits(0)
        elif predMode == PredictionMode.VERTICAL_PREDICTION:
            self.est_bits += self.cm.prediction_mode_bin1.estBits(1)
            self.est_bits += self.cm.prediction_mode_bin2.estBits(1)
            self.est_bits += self.cm.prediction_mode_bin3.estBits(1)

        # quant indexes
        self.add_bits_qindex_block(qIdxBlock)

        self.cm = org_probs
        return self.est_bits

    # similar to write_block_inter_pic but estimation only
    def est_block_bits_inter_pic(self, qIdxBlock):
        self.est_bits = 0
        org_probs = copy.deepcopy(self.cm)

        # side info: later

        # quant indexes
        self.add_bits_qindex_block(qIdxBlock)

        self.cm = org_probs
        return self.est_bits
